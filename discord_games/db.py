# 'g' is a global obj with a runtime of a single request
from flask import current_app, g
from psycopg2.pool import SimpleConnectionPool


def init_app(app):
    app.db = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=app.config['DB_URL']
    )
    # return connection after each request
    app.teardown_appcontext(close_conn)


def get_conn():
    if 'conn' not in g:
        g.conn = current_app.db.getconn()
    return g.conn


def close_conn(e=None):
    c = g.pop('conn', None)
    if c is not None:
        current_app.db.putconn(c)


def close_all():
    if hasattr(current_app, 'db'):
        current_app.db.closeall()
