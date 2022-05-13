import sys
import os

from aiohttp import web, test_utils
import pytest

# Paths for necessary imports
sys.path.append(os.path.normpath(os.path.abspath(__file__) + "../../../"))
sys.path.append(os.path.normpath(os.path.abspath(__file__) + "../../../src"))

from src.from_yaml import get_yaml  # noqa: E402

test_base_config = get_yaml('tests/test_data/test_db.yaml')['postgres']


@pytest.fixture
def unique_config():
    d = test_base_config
    d['database'] += "1"
    d['user'] += "1"
    d['password'] += "1"
    return d


@pytest.fixture
def prepare_app() -> web.Application:
    from jinja2 import FileSystemLoader
    from aiohttp_jinja2 import setup

    app = web.Application()
    setup(app, loader=FileSystemLoader('templates'))
    return app


@pytest.fixture
async def prepare_db(unique_config) -> None:
    from asyncpg import Connection, connect

    from init_db import setup_db

    test_config = unique_config

    await setup_db(test_db=test_config)

    yield test_config

    admin_dsn = 'postgres://postgres:postgres@localhost:5432/postgres'
    admin_conn: Connection = await connect(admin_dsn)

    await admin_conn.execute("DROP DATABASE IF EXISTS " +
                             f"{test_config['database']}")
    await admin_conn.execute(f"DROP ROLE IF EXISTS {test_config['user']}")
    await admin_conn.close()


async def test_connect_db(prepare_db) -> None:
    from asyncpg import Connection

    from src.db import connect_db

    test_config = prepare_db

    conn: Connection = await connect_db(test_db=test_config)

    assert conn.get_settings().session_authorization == test_config['user']

    row = await conn.fetchrow("""
        SELECT current_database();
    """)

    assert row['current_database'] == test_config['database']

    await conn.close()


async def test_insert_new_url(prepare_db) -> None:

    from src.db import connect_db, insert_new_url
    from init_db import create_table

    test_config = prepare_db

    await create_table(test_db=test_config)

    await insert_new_url('test_orig_url', 'test_short_url',
                         test_db=test_config)

    conn = await connect_db(test_db=test_config)
    row = await conn.fetchrow("""
        SELECT short_url, orig_url FROM urls
        WHERE short_url = 'test_short_url';
        """)

    assert {'short_url': 'test_short_url', 'orig_url': 'test_orig_url'} == \
        {i: j for i, j in row.items()}

    await conn.close()


async def test_select_url(prepare_db) -> None:

    from src.db import select_url, insert_new_url
    from init_db import create_table

    test_config = prepare_db

    await create_table(test_db=test_config)

    await insert_new_url('test_orig_url', 'test_short_url',
                         test_db=test_config)

    assert await select_url('test_short_url', test_db=test_config) == \
        'test_orig_url'
    assert await select_url('fake_url', test_db=test_config) is None


async def test_redir(
    prepare_app,
    prepare_db,
    aiohttp_client: test_utils.TestClient
) -> None:

    from src.views import redir
    from init_db import create_table
    from src.db import insert_new_url

    test_config = prepare_db

    app: web.Application = prepare_app()

    def foo(f):
        def bar(request):
            return f(request, test_db=test_config)
        return bar

    app.router.add_get(r'/{name:.+}', foo(redir))
    client: test_utils.TestClient = await aiohttp_client(app)
    await create_table(test_db=test_config)

    response = await client.get('/test_short_url')

    assert response.status == 404

    await insert_new_url('https://google.com', 'test_short_url',
                         test_db=test_config)
    response = await client.get('/test_short_url')

    assert response.status == 200


async def test_form_handler(
    prepare_app,
    prepare_db,
    aiohttp_client: test_utils.TestClient
) -> None:

    from aiohttp import ClientResponse
    from aiohttp_jinja2 import template

    from src.views import form_handler
    from src.db import select_url
    from init_db import create_table

    test_config = prepare_db

    app: web.Application = prepare_app()

    def foo(f):
        def bar(request):
            return f(request, test_db=test_config)
        return bar

    app.router.add_post('/', template('index.html')(foo(form_handler)))
    client: test_utils.TestClient = await aiohttp_client(app)
    await create_table(test_db=test_config)

    response: ClientResponse = await client.post('/', data={
        'short_url': 'test_short_url',
        'orig_url': 'https://www.google.com/'
    })
    assert response.status == 200
    row = await select_url('test_short_url', test_db=test_config)
    assert row == 'https://www.google.com/'
    text = await response.text()
    assert 'Your short URL: localhost:8080/test_short_url' in text

    response: ClientResponse = await client.post('/', data={
        'short_url': 'test_short_url',
        'orig_url': 'https://www.yandex.ru/'
    })
    assert response.status == 200
    text = await response.text()
    assert 'Short URL exists. Try again.' in text

    response: ClientResponse = await client.post('/', data={
        'short_url': '',
        'orig_url': 'https://www.yandex.ru/'
    })
    assert response.status == 200
    text = await response.text()
    assert 'Your short URL: localhost:8080/' in text

    response: ClientResponse = await client.post('/', data={
        'short_url': '',
        'orig_url': 'www.yandex.ru/'
    })
    assert response.status == 200
    text = await response.text()
    assert 'Please specify the network protocol.' in text
    assert 'For example: https://www.yandex.ru/' in text


async def test_index(
    prepare_app,
    aiohttp_client: test_utils.TestClient
) -> None:

    from src.views import index
    import os

    app: web.Application = prepare_app()
    app.router.add_get('/', index)
    client: test_utils.TestClient = await aiohttp_client(app)
    response = await client.get('/')

    assert response.status == 200

    with open(os.path.normpath(os.path.abspath(__file__) +
                               '/../test_data/index.html'), 'r') as f:
        text = await response.text()
        assert f.read() == text


def test_setup_routes() -> None:

    from src.routes import setup_routes

    app = web.Application()
    test_val = setup_routes(app)

    assert isinstance(app, web.Application)

    assert 'index' in app.router
    assert 'form_handler' in app.router
    assert 'redir' in app.router

    assert test_val is None
