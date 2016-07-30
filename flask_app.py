import config

import flask
import flask_sqlalchemy
import flask_restless
from sqlalchemy.ext.automap import automap_base


def create_api(flask_sqlalchemy_db, manager):
    Base = automap_base()
    Base.prepare(flask_sqlalchemy_db.engine, reflect=True)

    for table in Base.classes.keys():
        manager.create_api(Base.classes.get(table))


def make_app():
    app = flask.Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLA_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    db = flask_sqlalchemy.SQLAlchemy(app)

    manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
    create_api(db, manager)

    return app


if __name__ == '__main__':
    make_app().run()
