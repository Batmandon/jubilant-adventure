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
        columns = ", ".join(f"p.{c}" for c in PRODUCT_PUBLIC_COLUMNS)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {columns}, b.mrp, b.discount_percent
                FROM products p
                JOIN LATERAL (
                    SELECT mrp, discount_percent
                    FROM batches
                    WHERE product_id = p.id AND {SELLABLE_BATCH_CONDITION}
                    ORDER BY expiry_date, id
                    LIMIT 1
                ) b ON TRUE
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
            item["selling_price"] = selling_price(item["mrp"], item["discount_percent"])

        return {"items": items, "page": page, "page_size": page_size, "total": total}

    def get_products_by_name(self, name: str):
        search_term = name.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {", ".join(PRODUCT_PUBLIC_COLUMNS)}
                FROM products
                WHERE is_active = TRUE
                  AND name ILIKE %s ESCAPE '!'
                  AND {PRODUCT_IN_STOCK_CONDITION}
                ORDER BY name, id
                LIMIT %s
                """,
                (f"%{search_term}%", 50)
            )
            return cur.fetchall()

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
