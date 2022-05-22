"""Module for testing init_db.setup_db and init_db.create_table."""

import sys
import os

from asyncpg import connect, Connection

# Paths for necessary imports
sys.path.append(os.path.normpath(os.path.abspath(__file__) + "../../../"))
sys.path.append(os.path.normpath(os.path.abspath(__file__) + "../../../src"))

from src.from_yaml import get_yaml  # noqa: E402

test_config = get_yaml("tests/test_data/test_db.yaml")["postgres"]
admin_dsn = "postgres://postgres:postgres@localhost:5432/postgres"


async def test_setup_db() -> None:
    from init_db import setup_db

    test_dsn = "postgres://{user}:{password}@{host}:{port}/{database}".\
        format(**test_config)

    await setup_db(admin_dsn, test_db=test_config)

    conn = await connect(test_dsn)

    assert isinstance(conn, Connection)
    assert conn.get_settings().session_authorization == 'test_user'

    row = await conn.fetchrow('''
        SELECT current_database();
    ''')

    assert row['current_database'] == 'test_base'

    await conn.close()

    admin_conn: Connection = await connect(admin_dsn)

    await admin_conn.execute("DROP DATABASE IF EXISTS " +
                             f"{test_config['database']}")
    await admin_conn.execute(f"DROP ROLE IF EXISTS {test_config['user']}")
    await admin_conn.close()


async def test_create_table() -> None:

    from init_db import create_table, setup_db

    await setup_db(admin_dsn, test_db=test_config)

    await create_table(test_db=test_config)

    test_dsn = "postgres://{user}:{password}@{host}:{port}/{database}".\
        format(**test_config)

    conn: Connection = await connect(test_dsn)

    rows = await conn.fetch('''
        SELECT column_name, data_type, is_nullable
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'urls'
        ORDER BY column_name;
    ''')

    assert {'column_name': 'orig_url',
            'data_type': 'text',
            'is_nullable': 'NO'} == {i: j for i, j in rows[0].items()}
    assert {'column_name': 'short_url',
            'data_type': 'text',
            'is_nullable': 'NO'} == {i: j for i, j in rows[1].items()}

    row = await conn.fetchrow('''
        SELECT kcu.column_name, tc.constraint_type
        FROM INFORMATION_SCHEMA.table_constraints as tc
        JOIN INFORMATION_SCHEMA.key_column_usage as kcu
        ON kcu.constraint_name = tc.constraint_name
        WHERE kcu.table_name = 'urls';
    ''')

    assert {'column_name': 'short_url', 'constraint_type': 'PRIMARY KEY'} == \
        {i: j for i, j in row.items()}

    await conn.close()

    admin_conn: Connection = await connect(admin_dsn)

    await admin_conn.execute("DROP DATABASE IF EXISTS " +
                             f"{test_config['database']}")
    await admin_conn.execute(f"DROP ROLE IF EXISTS {test_config['user']}")
    await admin_conn.close()
