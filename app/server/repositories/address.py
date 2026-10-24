from auth import get_user
from models.Address_model import CreateAddress


class AddressRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_address(self, email: str, address: CreateAddress):
        with self.conn.cursor() as cur:
            user = get_user(cur, email, ("id",))
            if user is None:
                return {
                    "error": "Authenticated user no longer exists.",
                    "status_code": 401,
                }

            cur.execute(
                """
                INSERT INTO addresses (user_id, line, city, pincode, phone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, user_id, line, city, pincode, phone
                """,
                (
                    user["id"],
                    address.line,
                    address.city,
                    address.pincode,
                    address.phone,
                ),
            )
            return cur.fetchone()

    def list_addresses(self, email: str):
        with self.conn.cursor() as cur:
            user = get_user(cur, email, ("id",))
            if user is None:
                return {
                    "error": "Authenticated user no longer exists.",
                    "status_code": 401,
                }

            cur.execute(
                """
                SELECT id, line, city, pincode, phone
                FROM addresses
                WHERE user_id = %s
                ORDER BY id
                """,
                (user["id"],),
            )
            return {"items": cur.fetchall()}
