from aiohttp.web_app import Application
from aiohttp_jinja2 import template

from views import index, form_handler, redir

# Decoration that should have been in "views" module
form_handler = template('index.html')(form_handler)


def setup_routes(app: Application) -> None:
    app.router.add_get('/', index, name='index')
    app.router.add_post('/', form_handler, name='form_handler')
    app.router.add_get(r'/{name:.+}', redir, name='redir')
