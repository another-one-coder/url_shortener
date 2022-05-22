"""The module is responsible for interacting with the database."""

from os import getenv

from asyncpg import Connection, connect

from from_yaml import DATABASE_CONFIG


DATABASE_URL = getenv("DATABASE_URL")


async def connect_db(*, test_db: dict[str, str] | None = None) -> Connection:
    if DATABASE_URL is not None:
        user_dsn = DATABASE_URL
    else:
        db = test_db if test_db is not None else DATABASE_CONFIG['postgres']
        user_dsn = f"postgres://{db['user']}:{db['password']}" + \
            f"@{db['host']}:{db['port']}/{db['database']}"
    return await connect(user_dsn)


async def insert_new_url(
    orig_url: str,
    short_url: str,
    *,
    test_db: dict[str, str] | None = None
) -> None:
    conn: Connection = await connect_db(test_db=test_db)

    await conn.execute(f"""
        INSERT INTO urls ( short_url, orig_url )
            VALUES ( '{short_url}', '{orig_url}' );
    """)
    await conn.close()


async def select_url(
    short_url: str,
    *,
    test_db: dict[str, str] | None = None
) -> str | None:
    conn: Connection = await connect_db(test_db=test_db)

    row = await conn.fetchrow(f"""
        SELECT orig_url FROM urls
        WHERE short_url = '{short_url}'
    """)

    await conn.close()
    return row['orig_url'] if row is not None else None
