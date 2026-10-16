from models.Product_model import AddProduct, UpdateProduct


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
                SELECT {", ".join(PRODUCT_PUBLIC_COLUMNS)}
                FROM products
                WHERE {PRODUCT_IN_STOCK_CONDITION}
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (page_size, offset),
            )
            return cur.fetchall()

    def search_products(self, name: str):
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {", ".join(PRODUCT_PUBLIC_COLUMNS)}
                FROM products
                WHERE name ILIKE %s
                  AND {PRODUCT_IN_STOCK_CONDITION}
                """,
                (f"%{name}%",)
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
