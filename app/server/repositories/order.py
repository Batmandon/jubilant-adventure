from auth import get_user


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
