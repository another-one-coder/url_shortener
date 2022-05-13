from aiohttp import web
from jinja2 import FileSystemLoader
from aiohttp_jinja2 import setup

from routes import setup_routes

app = web.Application()
setup(app, loader=FileSystemLoader('templates'))
setup_routes(app)

web.run_app(app)
