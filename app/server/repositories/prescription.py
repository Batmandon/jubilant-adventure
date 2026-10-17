from auth import get_user


class PrescriptionRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_user_id(self, email: str):
        with self.conn.cursor() as cur:
            user = get_user(cur, email, ("id",))
            return user["id"] if user is not None else None

    def create_prescription(self, user_id: int, file_path: str):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO prescriptions (user_id, file_path)
                VALUES (%s, %s)
                RETURNING id, status, created_at
                """,
                (user_id, file_path),
            )
            return cur.fetchone()
