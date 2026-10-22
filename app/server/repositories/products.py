from models.Product_model import AddProduct, UpdateProduct
from repositories.pricing import selling_price

PRODUCT_PUBLIC_COLUMNS = (
    "id",
    "name",
    "strength",
    "form",
    "pack_size",
    "schedule",
    "gst_percent",
    "storage_condition",
    "description",
    "image_url",
)

SELLABLE_BATCH_CONDITION = "quantity > 0 AND expiry_date > CURRENT_DATE"

PRODUCT_CARD_SELECT = """
    p.id,
    p.name,
    p.strength,
    p.form,
    p.pack_size,
    p.schedule,
    p.requires_prescription,
    p.gst_percent,
    p.storage_condition,
    p.description,
    p.image_url,
    c.name AS category,
    br.name AS brand,
    m.name AS manufacturer,
    COALESCE(
        s.name,
        (
            SELECT string_agg(salt.name, ', ' ORDER BY salt.name)
            FROM product_salts ps
            JOIN salts salt ON salt.id = ps.salt_id
            WHERE ps.product_id = p.id
        )
    ) AS salt,
    b.mrp,
    b.discount_percent,
    b.discount_percent AS discount_percentage,
    b.quantity
"""

PRODUCT_CARD_JOINS = f"""
    LEFT JOIN categories c ON c.id = p.category_id
    LEFT JOIN brands br ON br.id = p.brand_id
    LEFT JOIN manufacturers m ON m.id = p.manufacturer_id
    LEFT JOIN salts s ON s.id = p.salt_id
    JOIN LATERAL (
        SELECT mrp, discount_percent, quantity
        FROM batches
        WHERE product_id = p.id AND {SELLABLE_BATCH_CONDITION}
        ORDER BY expiry_date, id
        LIMIT 1
    ) b ON TRUE
"""

PRODUCT_IN_STOCK_CONDITION = """
    EXISTS (
        SELECT 1
        FROM batches b
        WHERE b.product_id = products.id
          AND b.quantity > 0
          AND b.expiry_date >= CURRENT_DATE
    )
"""

class ProductRepository:
    def __init__(self, conn):
        self.conn = conn

    def add_product(self, product: AddProduct):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (name, strength, form, pack_size, schedule, gst_percent, hsn_code, storage_condition, description, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    product.name,
                    product.strength,
                    product.form,
                    product.pack_size,
                    product.schedule,
                    product.gst_percent,
                    product.hsn_code,
                    product.storage_condition,
                    product.description,
                    product.image_url
                )
            )
            return {"id": cur.fetchone()["id"]}

    def update_product(self, product_id: int, product: UpdateProduct):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET name = %s, strength = %s, form = %s, pack_size = %s, schedule = %s, gst_percent = %s, hsn_code = %s, storage_condition = %s, description = %s, image_url = %s
                WHERE id = %s
                """,
                (
                    product.name,
                    product.strength,
                    product.form,
                    product.pack_size,
                    product.schedule,
                    product.gst_percent,
                    product.hsn_code,
                    product.storage_condition,
                    product.description,
                    product.image_url,
                    product_id
                )
            )
            if cur.rowcount == 0:
                return {"error": f"Product with ID {product_id} does not exist."}
            return {"updated": True}

    def delete_product(self, product_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM products
                WHERE id = %s
                """,
                (product_id,)
            )
            if cur.rowcount == 0:
                return {"error": f"Product with ID {product_id} does not exist."}
            return {"deleted": True}

    def get_product(self, product_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {", ".join(PRODUCT_PUBLIC_COLUMNS)}
                FROM products
                WHERE id = %s
                  AND {PRODUCT_IN_STOCK_CONDITION}
                """,
                (product_id,)
            )
            return cur.fetchone()

    def list_products(self, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {PRODUCT_CARD_SELECT}
                FROM products p
                {PRODUCT_CARD_JOINS}
                WHERE p.is_active = TRUE
                ORDER BY p.name, p.id
                LIMIT %s OFFSET %s
                """,
                (page_size, offset),
            )
            items = cur.fetchall()

            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM products p
                WHERE p.is_active = TRUE
                AND EXISTS (
                    SELECT 1 FROM batches
                    WHERE product_id = p.id AND {SELLABLE_BATCH_CONDITION}
                )
                """
            )
            total = cur.fetchone()["total"]

        for item in items:
            item["selling_price"] = (
                selling_price(item["mrp"], item["discount_percent"])
                if item["mrp"] is not None
                else None
            )

        return {"items": items, "page": page, "page_size": page_size, "total": total}

    def get_products_by_name(self, name: str, page: int = 1, page_size: int = 20):
        search_term = name.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        offset = (page - 1) * page_size
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {PRODUCT_CARD_SELECT}
                FROM products p
                {PRODUCT_CARD_JOINS}
                WHERE p.is_active = TRUE
                  AND p.name ILIKE %s ESCAPE '!'
                ORDER BY p.name, p.id
                LIMIT %s
                OFFSET %s
                """,
                (f"%{search_term}%", page_size, offset)
            )
            items = cur.fetchall()

            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM products p
                WHERE p.is_active = TRUE
                  AND p.name ILIKE %s ESCAPE '!'
                  AND EXISTS (
                      SELECT 1 FROM batches b
                      WHERE b.product_id = p.id AND {SELLABLE_BATCH_CONDITION}
                  )
                """,
                (f"%{search_term}%",)
            )
            total = cur.fetchone()["total"]

        for item in items:
            item["selling_price"] = (
                selling_price(item["mrp"], item["discount_percent"])
                if item["mrp"] is not None
                else None
            )

        return {"items": items, "page": page, "page_size": page_size, "total": total}

    def get_products_by_category(self, category_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {", ".join(PRODUCT_PUBLIC_COLUMNS)}
                FROM products
                WHERE category_id = %s
                  AND {PRODUCT_IN_STOCK_CONDITION}
                """,
                (category_id,)
            )
            return cur.fetchall()

    def get_products_by_brand(self, brand_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {", ".join(PRODUCT_PUBLIC_COLUMNS)}
                FROM products
                WHERE brand_id = %s
                  AND {PRODUCT_IN_STOCK_CONDITION}
                """,
                (brand_id,)
            )
            return cur.fetchall()
