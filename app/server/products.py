from models.Product_model import AddProduct, UpdateProduct

class MedicineService:
    def __init__(self, conn):
        self.conn = conn

    def add_product(self, product: AddProduct):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (name, strength, form, pack_size, schedule, gst_percent, hsn_code, storage_condition, description, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    product.name,
                    product.strength,
                    product.form,
                    product.pack_size,
                    product.scheduling,
                    product.gst_percent,
                    product.hsn_code,
                    product.storage_condition,
                    product.description,
                    product.image_url
                )
            )

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
                    product.scheduling,
                    product.gst_percent,
                    product.hsn_code,
                    product.storage_condition,
                    product.description,
                    product.image_url,
                    product_id
                )
            )

    def delete_product(self, product_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM products
                WHERE id = %s
                """,
                (product_id,)
            )
