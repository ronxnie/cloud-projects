from flask import Flask

from .config import Config
from .db import init_db
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)
    app.register_blueprint(bp)

    return app
