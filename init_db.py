"""
Module for creation the database for the application.
But beacause the application runs on heroku, it is used only to create
test databases on local machine.
"""

from asyncpg import Connection, connect
from asyncio import run

from src.from_yaml import DATABASE_CONFIG

ADMIN_DSN = 'postgres://postgres:postgres@localhost:5432/postgres'


async def setup_db(
    admin_dsn: str = ADMIN_DSN,
    *,
    test_db: dict | None = None
) -> None:
    """The function that creates a database.  Uses admin DSN."""

    db = test_db if test_db else DATABASE_CONFIG['postgres']

    conn: Connection = await connect(admin_dsn)
    await conn.execute(f"DROP DATABASE IF EXISTS {db['database']}")
    await conn.execute(f"DROP ROLE IF EXISTS {db['user']}")
    await conn.execute(f"CREATE USER {db['user']} WITH PASSWORD " +
                       f"'{db['password']}'")
    await conn.execute(f"CREATE DATABASE {db['database']}")
    await conn.execute("GRANT ALL PRIVILEGES ON DATABASE " +
                       f"{db['database']} TO {db['user']}")
    await conn.close()


async def create_table(*, test_db: dict | None = None) -> None:
    """
    The function that creates the table in the database
    for storing short and original URLs.
    """

    db = test_db if test_db else DATABASE_CONFIG['postgres']

    user_dsn = 'postgres://{user}:{password}@{host}:{port}/{database}'.\
        format(**db)

    conn: Connection = await connect(user_dsn)
    await conn.execute("""
        CREATE TABLE urls
        (
            short_url text NOT NULL,
            orig_url text NOT NULL,
            PRIMARY KEY ( short_url )
        )
    """)
    await conn.close()


async def main():
    await setup_db()
    await create_table()


if __name__ == '__main__':
    run(main())
