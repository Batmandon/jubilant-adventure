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

    def get_product_details(self, product_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.name, p.strength, p.form, p.pack_size, p.schedule,
                       p.description, p.image_url, p.storage_condition,
                       br.name AS brand, c.name AS category,
                       COALESCE(stock.available_quantity, 0) AS available_quantity,
                       (COALESCE(stock.available_quantity, 0) > 0) AS in_stock,
                       price.mrp, price.discount_percent,
                       pd.description_uses, pd.side_effects_warnings,
                       pd.dosage_information, pd.storage_care,
                       pd.information_source, pd.last_reviewed_at
                FROM products p
                LEFT JOIN brands br ON br.id = p.brand_id
                LEFT JOIN categories c ON c.id = p.category_id
                LEFT JOIN product_details pd ON pd.product_id = p.id
                LEFT JOIN LATERAL (
                    SELECT SUM(b.quantity) AS available_quantity
                    FROM batches b
                    WHERE b.product_id = p.id
                      AND b.quantity > 0
                      AND b.expiry_date >= CURRENT_DATE
                ) stock ON TRUE
                LEFT JOIN LATERAL (
                    SELECT b.mrp, b.discount_percent
                    FROM batches b
                    WHERE b.product_id = p.id
                      AND b.quantity > 0
                      AND b.expiry_date >= CURRENT_DATE
                    ORDER BY b.expiry_date, b.id
                    LIMIT 1
                ) price ON TRUE
                WHERE p.id = %s AND p.is_active = TRUE
                """,
                (product_id,),
            )
            product = cur.fetchone()

        if product is None:
            return None

        product["price"] = (
            selling_price(product["mrp"], product["discount_percent"])
            if product["mrp"] is not None
            else None
        )
        return product

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

    def search_products(self, search_term: str, page: int = 1, page_size: int = 20):
        search_term = search_term.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        pattern = f"%{search_term}%"
        offset = (page - 1) * page_size
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {PRODUCT_CARD_SELECT}
                FROM products p
                {PRODUCT_CARD_JOINS}
                WHERE p.is_active = TRUE
                  AND (
                      p.name ILIKE %s ESCAPE '!'
                      OR br.name ILIKE %s ESCAPE '!'
                      OR c.name ILIKE %s ESCAPE '!'
                  )
                ORDER BY p.name, p.id
                LIMIT %s
                OFFSET %s
                """,
                (pattern, pattern, pattern, page_size, offset)
            )
            items = cur.fetchall()

            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM products p
                WHERE p.is_active = TRUE
                  AND (
                      p.name ILIKE %s ESCAPE '!'
                      OR EXISTS (
                          SELECT 1 FROM brands br
                          WHERE br.id = p.brand_id
                            AND br.name ILIKE %s ESCAPE '!'
                      )
                      OR EXISTS (
                          SELECT 1 FROM categories c
                          WHERE c.id = p.category_id
                            AND c.name ILIKE %s ESCAPE '!'
                      )
                  )
                  AND EXISTS (
                      SELECT 1 FROM batches b
                      WHERE b.product_id = p.id AND {SELLABLE_BATCH_CONDITION}
                  )
                """,
                (pattern, pattern, pattern)
            )
            total = cur.fetchone()["total"]

        for item in items:
            item["selling_price"] = (
                selling_price(item["mrp"], item["discount_percent"])
                if item["mrp"] is not None
                else None
            )

        return {"items": items, "page": page, "page_size": page_size, "total": total}
