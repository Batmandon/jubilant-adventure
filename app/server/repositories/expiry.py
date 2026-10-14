class BatchRepository:
    def __init__(self, conn):
        self.conn = conn

    def list_expiry(self, *, expired: bool, within_days: int = 90,
                    page: int = 1, page_size: int = 20):
        page_size = min(page_size, 100)
        offset = (page - 1) * page_size

        if expired:
            cond = "b.expiry_date < CURRENT_DATE"
            params = ()
            order = "b.expiry_date DESC, b.id"
        else:
            cond = ("b.expiry_date >= CURRENT_DATE "
                    "AND b.expiry_date <= CURRENT_DATE + %s::int")
            params = (within_days,)
            order = "b.expiry_date ASC, b.id"

        base = f"""
            FROM batches b
            JOIN products p ON p.id = b.product_id
            WHERE {cond} AND b.quantity > 0 AND p.is_active = TRUE
        """

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT p.id AS product_id, p.name, b.id AS batch_id, b.batch_no,
                       b.expiry_date, b.quantity,
                       (b.expiry_date - CURRENT_DATE) AS days_left
                {base}
                ORDER BY {order}
                LIMIT %s OFFSET %s
                """,
                (*params, page_size, offset),
            )
            items = cur.fetchall()
            for item in items:
                item["status"] = expiry_status(item["days_left"])

            cur.execute(f"SELECT COUNT(*) AS total {base}", params)
            total = cur.fetchone()["total"]

        return {"items": items, "page": page, "page_size": page_size, "total": total}


def expiry_status(days_left: int) -> str:
    if days_left < 0:
        return "expired"
    if days_left <= 30:
        return "critical"
    if days_left <= 60:
        return "warning"
    if days_left <= 90:
        return "soon"
    return "ok"
