from functools import wraps
from db import db


def sessionhandler(obj):
    @wraps(obj)
    def wrapped(*args, **kwargs):
        session = db.Session()
        kwargs['session'] = session
        func = obj(*args, **kwargs)
        session.close()
        return func
    return wrapped

