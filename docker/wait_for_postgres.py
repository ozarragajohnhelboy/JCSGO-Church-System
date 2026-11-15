"""Wait until PostgreSQL accepts connections."""
import os
import sys
import time

import psycopg2


def main() -> int:
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = os.environ.get("POSTGRES_DB", "jcsgo")
    user = os.environ.get("POSTGRES_USER", "jcsgo")
    password = os.environ.get("POSTGRES_PASSWORD", "")

    for attempt in range(1, 31):
        try:
            connection = psycopg2.connect(
                dbname=name,
                user=user,
                password=password,
                host=host,
                port=port,
            )
            connection.close()
            print("PostgreSQL is ready.")
            return 0
        except Exception as exc:
            print(f"Waiting for PostgreSQL ({attempt}/30): {exc}")
            time.sleep(1)

    print("PostgreSQL did not become ready in time.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
