from flask_restful import Resource, reqparse
from db.models import Account, Strategy, UserAccountLink, StrategyUserLink
from flask_jwt_extended import get_jwt_identity, jwt_required
from resources.helpers import sessionhandler, useraccountrightsneeded
from dateutil.tz import gettz


class Accounts(Resource):
    @jwt_required()
    @sessionhandler
    def get(self, session):
        accounts = Account.getaccountsbyuserid(session=session, userid=get_jwt_identity())

        return [self._returndictforaccount(session=session, account=x) for x in accounts]

    @jwt_required()
    @sessionhandler
    @useraccountrightsneeded(editrights=True)
    def put(self, session, account):
        parser = reqparse.RequestParser()
        parser.add_argument("accountid", required=True, type=int)
        parser.add_argument("executingstrategyid", required=False, type=int)
        parser.add_argument("accountname", required=False)
        parser.add_argument("isactive", required=False)

        data = parser.parse_args()

        if not Strategy.canuserusestrategy(session=session,
                                           userid=get_jwt_identity(),
                                           strategyid=int(data['executingstrategyid'])):
            return {"message": "User cannot use strategy"}, 401

        if data['executingstrategyid']:
            account.executingstrategy = int(data['executingstrategyid'])

        if data['accountname']:
            account.name = data['accountname']

        if data['isactive']:
            account.isactive = bool(data['isactive'])

        session.commit()

        return self._returndictforaccount(session=session, account=account)

    @jwt_required()
    @sessionhandler
    def post(self, session):
        parser = reqparse.RequestParser()
        parser.add_argument("accountname", required=True)
        parser.add_argument("accountid", required=True)
        parser.add_argument("currency", required=True)
        parser.add_argument("timezone", required=True)
        parser.add_argument("executingstrategyid", required=False)

        data = parser.parse_args()

        newaccount = Account()
        newaccount.name = data['accountname']
        newaccount.accountid = data['accountid']
        newaccount.currency = data['currency']
        try:
            newaccount.timezone = gettz(data['timezone'])
        except ValueError:
            return {"message": "Invalid timezone"}, 400
        newaccount.executingstrategy = data['executingstrategyid']
        newaccount.isactive = True

        session.add(newaccount)
        session.flush([newaccount])

        # Add account to user
        newlink = UserAccountLink()
        newlink.userid = get_jwt_identity()
        newlink.accountid = newaccount.id
        newlink.isowner = True

        session.add(newlink)

        session.commit()

        return self._returndictforaccount(session=session, account=newaccount)

    @staticmethod
    def _returndictforaccount(session, account: Account) -> dict:
        strategy = Strategy.getstrategywithid(session=session, id=account.executingstrategy)

        return {
            "id": account.id,
            "accountname": account.name,
            "accountid": account.accountid,
            "currency": account.currency,
            "timezone": account.timezone,
            "executingstrategyid": account.executingstrategy,
            "executingstrategyname": strategy.name if strategy else None,
            "isactive": account.isactive
        }
