from models.Product_model import AddProduct, UpdateProduct
from auth import get_user, get_current_user, require_admin
class MedicineService:
    def __init__(self, conn):
        self.conn = conn

    def add_product(self, product: AddProduct, token: str):
        with self.conn.cursor() as cur:
            payload = get_current_user(token)
            is_admin = require_admin(payload)

            if get_user(cur, payload["sub"]) is None or is_admin["role"] != "admin":
                return {"error": "Unauthorized access. Admin privileges required."}

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

    def update_product(self, product_id: int, product: UpdateProduct, token: str):
        with self.conn.cursor() as cur:
            payload = get_current_user(token)
            is_admin = require_admin(payload)
            if get_user(cur, payload["sub"]) is None or is_admin["role"] != "admin":
                return {"error": "Unauthorized access. Admin privileges required."}

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

    def delete_product(self, product_id: int, token: str):
        with self.conn.cursor() as cur:
            payload = get_current_user(token)
            is_admin = require_admin(payload)

            if get_user(cur, payload["sub"]) is None or is_admin["role"] != "admin":
                return {"error": "Unauthorized access. Admin privileges required."}

            if cur.rowcount == 0:
                raise ValueError(f"Product with ID {product_id} does not exist.")
            cur.execute(
                """
                DELETE FROM products
                WHERE id = %s
                """,
                (product_id,)
            )

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

    def list_products(self):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM products
                """
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
