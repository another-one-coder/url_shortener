from random import choices
from string import ascii_letters, digits
from os import getenv

from aiohttp.web import Request, HTTPFound, HTTPNotFound
from aiohttp_jinja2 import template

from db import insert_new_url, select_url
from from_yaml import PROTOCOLS


APP_URL = getenv("APP_URL")


@template('index.html')
async def index(request: Request) -> dict:
    return {}


# @template decorator is not used here, because it does not allow
# testing a function with a test database.  Or I just don't know how to
# do it with it.  The decoration is carried out in the "routes" module
# before registering the routes.
async def form_handler(
        request: Request,
        *,
        test_db: dict[str, str] | None = None
) -> dict:
    data = await request.post()

    possible_url = await select_url(data['short_url'], test_db=test_db)

    if possible_url is not None:
        return {'warn': 'Short URL exists. Try again.'}

    if not any(map(data['orig_url'].startswith,
                   (i + '://' for i in PROTOCOLS))):
        return {'warn': 'Please specify the network protocol. ' +
                        f'For example: https://{data["orig_url"]}'}

    if str(data['short_url']) == '':
        short_url = "".join(choices(ascii_letters + digits, k=6))
    else:
        short_url = str(data['short_url'])

    await insert_new_url(data['orig_url'], short_url, test_db=test_db)

    return {'short_url': f'{APP_URL}/' + short_url}


async def redir(
    request: Request,
    *,
    test_db: dict[str, str] | None = None
) -> None:
    url = str(request.rel_url)
    if url != '/favicon.ico':
        orig_url = await select_url(url[1:], test_db=test_db)
        raise HTTPFound(orig_url) if orig_url is not None else HTTPNotFound()
