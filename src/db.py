from asyncpg import Connection, connect

from from_yaml import DATABASE_CONFIG


async def connect_db(*, test_db: dict[str, str] | None = None) -> Connection:

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

    if test_db is not None:
        conn: Connection = await connect_db(test_db=test_db)
    else:
        conn: Connection = await connect_db()

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

    if test_db is not None:
        conn: Connection = await connect_db(test_db=test_db)
    else:
        conn: Connection = await connect_db()

    row = await conn.fetchrow(f"""
        SELECT orig_url FROM urls
        WHERE short_url = '{short_url}'
    """)

    await conn.close()
    return row['orig_url'] if row is not None else None
