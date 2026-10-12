from auth import get_user, get_current_user, require_admin

def get_products_expiry(conn, token: str, page: int, page_size: int):
    offset = (page - 1) * page_size
    with conn.cursor() as cur:
        payload = get_current_user(token)
        is_admin = require_admin(payload)

        if get_user(cur, payload["sub"]) is None or is_admin["role"] != "admin":
            return {"error": "Unauthorized access. Admin privileges required."}

        cur.execute(
            """
            SELECT name, expiry_date, quantity
            FROM batches left join products p on batches.product_id = p.id
            WHERE expiry_date < CURRENT_DATE
            ORDER BY expiry_date ASC, batches.id ASC
            LIMIT %s OFFSET %s
            """,
            (page_size, offset)
        )

        items = cur.fetchall()
        cur.execute("SELECT COUNT(*) as total_expired FROM batches WHERE expiry_date < CURRENT_DATE")
        total_expired = cur.fetchone()["total_expired"]
        return {"items": items,"page": page, "page_size": page_size, "total_expired": total_expired}


def get_nearest_expiry(conn, token: str, page: int, page_size: int):
    offset = (page - 1) * page_size
    with conn.cursor() as cur:
        payload = get_current_user(token)
        is_admin = require_admin(payload)

        if get_user(cur, payload["sub"]) is None or is_admin["role"] != "admin":
            return {"error": "Unauthorized access. Admin privileges required."}

        cur.execute(
            """
            SELECT name, expiry_date, quantity
            FROM batches left join products p on batches.product_id = p.id
            WHERE expiry_date >= CURRENT_DATE
            ORDER BY expiry_date ASC
            LIMIT %s OFFSET %s
            """,
            (page_size, offset)
        )
        items = cur.fetchall()
        if not items:
            return {"message": "No products found with nearest expiry dates."}

        cur.execute("SELECT COUNT(*) as total_nearest FROM batches WHERE expiry_date >= CURRENT_DATE")
        total_nearest = cur.fetchone()["total_nearest"]

        return {"items": items, "page": page, "page_size": page_size, "total_nearest": total_nearest}


def expiry_status(items: dict):
    expiry_date = items["expiry_date"]
    if expiry_date <=90:
        return "good"
    elif expiry_date <= 60:
        return "dangerxone"

    else:
        return "dangerzone"
