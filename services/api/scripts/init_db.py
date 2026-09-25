"""Initialize the Postgres database using the SQL migration file.

This script connects to DATABASE_URL and executes the SQL in migrations/0001_initial.sql.
"""
import os
import psycopg2

SQL_PATH = os.path.join(os.path.dirname(__file__), "..", "migrations", "0001_initial.sql")
SQL_PATH = os.path.abspath(SQL_PATH)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/balcony_dev"
)


def main():
    with open(SQL_PATH, "r", encoding="utf-8") as fh:
        sql = fh.read()

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.close()
    print("Database initialized from", SQL_PATH)


if __name__ == "__main__":
    main()
