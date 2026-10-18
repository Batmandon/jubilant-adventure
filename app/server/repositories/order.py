from auth import get_user
from decimal import Decimal
from repositories.pricing import selling_price

# Schedules that need a prescription. Orders with these are blocked until the
# prescription flow is built.
RX_SCHEDULES = {"H", "H1", "X"}


class OrderError(Exception):
    """Base class for expected order problems. The router maps these to HTTP errors."""


class AddressNotFound(OrderError):
    pass


class EmptyCart(OrderError):
    pass


class OutOfStock(OrderError):
    def __init__(self, product_name: str):
        super().__init__(product_name)
        self.product_name = product_name


class MissingBatchPrice(OrderError):
    def __init__(self, product_name: str):
        super().__init__(product_name)
        self.product_name = product_name


class PrescriptionRequired(OrderError):
    def __init__(self, product_name: str):
        super().__init__(product_name)
        self.product_name = product_name


class OrderRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_user_id(self, email: str):
        with self.conn.cursor() as cur:
            user = get_user(cur, email, ("id",))
            return user["id"] if user is not None else None

    def add_cart_item(self, user_id: int, product_id: int, quantity: int):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, is_active FROM products WHERE id = %s FOR UPDATE",
                (product_id,),
            )
            product = cur.fetchone()
            if product is None:
                return {
                    "error": f"Product with ID {product_id} does not exist.",
                    "status_code": 404,
                }
            if not product["is_active"]:
                return {
                    "error": f"Product with ID {product_id} is not available.",
                    "status_code": 409,
                }

            cur.execute(
                """
                SELECT COALESCE(SUM(quantity), 0) AS available_stock
                FROM batches
                WHERE product_id = %s
                  AND quantity > 0
                  AND expiry_date >= CURRENT_DATE
                """,
                (product_id,),
            )
            available_stock = cur.fetchone()["available_stock"]

            cur.execute(
                """
                SELECT quantity
                FROM cart_items
                WHERE user_id = %s AND product_id = %s
                FOR UPDATE
                """,
                (user_id, product_id),
            )
            existing = cur.fetchone()
            requested_total = quantity + (existing["quantity"] if existing else 0)
            if requested_total > available_stock:
                return {
                    "error": (
                        f"Only {available_stock} units of product ID {product_id} "
                        "are currently available."
                    ),
                    "status_code": 409,
                }

            cur.execute(
                """
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                RETURNING id, user_id, product_id, quantity
                """,
                (user_id, product_id, quantity),
            )
            return cur.fetchone()

    def place_order(self, user_id: int, address_id: int, payment_method: str) -> dict:
        # Everything below is one transaction: if anything raises, nothing is saved.
        with self.conn.transaction():
            with self.conn.cursor() as cur:
                # 1. Address must belong to this user
                cur.execute(
                    """
                    SELECT line, city, pincode, phone
                    FROM addresses
                    WHERE id = %s AND user_id = %s
                    """,
                    (address_id, user_id),
                )
                addr = cur.fetchone()
                if addr is None:
                    raise AddressNotFound()

                # 2. Read the cart (ORDER BY product_id keeps lock order consistent)
                cur.execute(
                    """
                    SELECT c.product_id, c.quantity, p.name, p.schedule, p.is_active
                    FROM cart_items c
                    JOIN products p ON p.id = c.product_id
                    WHERE c.user_id = %s
                    ORDER BY c.product_id
                    """,
                    (user_id,),
                )
                cart = cur.fetchall()
                if not cart:
                    raise EmptyCart()

                # 3. Pick batches (earliest expiry first) and lock them
                lines = []  # (product_id, batch_id, quantity, unit_price)
                total = Decimal("0")

                for item in cart:
                    if not item["is_active"]:
                        raise OutOfStock(item["name"])
                    if item["schedule"] in RX_SCHEDULES:
                        raise PrescriptionRequired(item["name"])

                    needed = item["quantity"]
                    cur.execute(
                        """
                        SELECT id, quantity, mrp, discount_percent
                        FROM batches
                        WHERE product_id = %s
                          AND quantity > 0
                          AND expiry_date >= CURRENT_DATE
                        ORDER BY expiry_date, id
                        FOR UPDATE
                        """,
                        (item["product_id"],),
                    )
                    for batch in cur.fetchall():
                        if batch["mrp"] is None:
                            raise MissingBatchPrice(item["name"])
                        sp = selling_price(batch["mrp"], batch["discount_percent"])
                        take = min(needed, batch["quantity"])
                        lines.append(
                            (
                                item["product_id"],
                                batch["id"],
                                take,
                                sp,
                                batch["mrp"],
                                batch["discount_percent"],
                            )
                        )
                        total += sp * take
                        needed -= take
                        if needed == 0:
                            break

                    if needed > 0:
                        raise OutOfStock(item["name"])

                # 4. Insert the order (address copied as a snapshot)
                cur.execute(
                    """
                    INSERT INTO orders (user_id, status, address, total, payment_method)
                    VALUES (
                        %s,
                        'pending',
                        jsonb_build_object(
                            'line', %s::text,
                            'city', %s::text,
                            'pincode', %s::text,
                            'phone', %s::text
                        ),
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        user_id,
                        addr["line"],
                        addr["city"],
                        addr["pincode"],
                        addr["phone"],
                        total,
                        payment_method,
                    ),
                )
                order_id = cur.fetchone()["id"]

                # 5. Insert order_items with the price frozen at order time
                cur.executemany(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, batch_id, quantity, unit_price,
                        mrp, discount_percent
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (order_id, product_id, batch_id, quantity, price, mrp, discount)
                        for (
                            product_id,
                            batch_id,
                            quantity,
                            price,
                            mrp,
                            discount,
                        ) in lines
                    ],
                )

                # 6. Deduct stock from the locked batches
                cur.executemany(
                    "UPDATE batches SET quantity = quantity - %s WHERE id = %s",
                    [
                        (quantity, batch_id)
                        for _, batch_id, quantity, _, _, _ in lines
                    ],
                )

                # 7. Empty the cart
                cur.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))

        return {"order_id": order_id, "total": total}

    def list_orders(self, user_id: int, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, total, payment_method, created_at
                FROM orders
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, page_size, offset),
            )
            items = cur.fetchall()

            cur.execute(
                "SELECT COUNT(*) AS total FROM orders WHERE user_id = %s",
                (user_id,),
            )
            total = cur.fetchone()["total"]

        return {"items": items, "page": page, "page_size": page_size, "total": total}

    def get_order(self, order_id: int, user_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, address, total, payment_method, created_at
                FROM orders
                WHERE id = %s AND user_id = %s
                """,
                (order_id, user_id),
            )
            order = cur.fetchone()
            if order is None:
                return None

            cur.execute(
                """
                SELECT p.name, b.batch_no, oi.quantity, oi.unit_price,
                       oi.mrp, oi.discount_percent
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                JOIN batches b ON b.id = oi.batch_id
                WHERE oi.order_id = %s
                ORDER BY oi.id
                """,
                (order_id,),
            )
            order["items"] = cur.fetchall()

        return order