from functools import wraps
from db import db
from db.models import Account
from flask_jwt_extended import get_jwt_identity
from flask_restful import reqparse
from flask import request


def sessionhandler(obj):
    @wraps(obj)
    def wrapped(*args, **kwargs):
        session = db.Session()
        kwargs['session'] = session
        func = obj(*args, **kwargs)
        session.close()
        return func
    return wrapped


def useraccountrightsneeded(editrights=False):
    def wrapper(obj):
        @wraps(obj)
        def wrapped(*args, **kwargs):
            session = kwargs['session']
            parser = reqparse.RequestParser()
            parser.add_argument("accountid",
                                required=True,
                                type=int,
                                location="args" if not request.content_type == "application/json" else "json")

            data = parser.parse_args()

            accounts = Account.getaccountsbyuserid(session=session, userid=get_jwt_identity())
            try:
                account = next(x for x in accounts if x.id == int(data['accountid']))
            except StopIteration:
                return {"message": "Account not found"}, 404

            if editrights:
                if not account.canusereditaccount(session=session, userid=get_jwt_identity(), accountid=account.id):
                    return {"message": "User not allowed to edit account"}, 403
            # Add account to kwargs to be used in the function
            kwargs['account'] = account
            func = obj(*args, **kwargs)
            return func
        return wrapped
    return wrapper

