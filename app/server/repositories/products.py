from models.Product_model import AddProduct, UpdateProduct


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
                """
                SELECT * FROM products
                WHERE id = %s
                """,
                (product_id,)
            )
            return cur.fetchone()

    def list_products(self, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM products
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (page_size, offset),
            )
            return cur.fetchall()

    def search_products(self, name: str):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM products
                WHERE name ILIKE %s
                """,
                (f"%{name}%",)
            )
            return cur.fetchall()

    def get_products_by_category(self, category_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM products
                WHERE category_id = %s
                """,
                (category_id,)
            )
            return cur.fetchall()

    def get_products_by_brand(self, brand_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM products
                WHERE brand_id = %s
                """,
                (brand_id,)
            )
            return cur.fetchall()
