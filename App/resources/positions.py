import datetime
from flask_restful import Resource, reqparse
from db.models import Account, Position
from flask_jwt_extended import get_jwt_identity, jwt_required
from resources.helpers import sessionhandler, useraccountrightsneeded
from dateutil.parser import parse
from dateutil.tz import gettz
from supporting.performancecalculator import PerformanceCalculator


class Positions(Resource):
    @jwt_required()
    @sessionhandler
    @useraccountrightsneeded()
    def get(self, session, account: Account):
        parser = reqparse.RequestParser()
        parser.add_argument("onlyopen", type=int, location="args", required=False)

        data = parser.parse_args()

        if data['onlyopen'] and bool(data['onlyopen']) is True:
            return [self._positiontodict(x) for x in Position.getopenpositionsforaccount(session=session,
                                                                                         accountid=account.id)]
        return [self._positiontodict(x) for x in Position.getallpositionsforaccount(session=session,
                                                                                    accountid=account.id)]

    @jwt_required()
    @sessionhandler
    @useraccountrightsneeded(editrights=True)
    def post(self, session, account: Account):
        parser = reqparse.RequestParser()
        parser.add_argument("brokerpositionid", required=True)
        parser.add_argument("brokerinstrumentidentifier", required=True)
        parser.add_argument("instrumentname", required=True)
        parser.add_argument("status", required=True)
        parser.add_argument("expirydate", required=False)
        parser.add_argument("size", required=True)
        parser.add_argument("entrydatetime", required=True)
        parser.add_argument("entryprice", required=True)
        parser.add_argument("stoplossprice", required=True)
        parser.add_argument("takeprofitprice", required=True)
        parser.add_argument("exitdatetime", required=False)
        parser.add_argument("exitprice", required=False)
        parser.add_argument("profit", required=False)

        data = parser.parse_args()

        dbpos = Position.getpositionwithaccountandbrokerid(session=session,
                                                           accountid=account.id,
                                                           brokerpositionid=data['brokerpositionid'])
        if not dbpos:
            dbpos = Position()
            dbpos.accountid = account.id
            dbpos.brokerpositionid = data['brokerpositionid']

            session.add(dbpos)

        dbpos.instrumentname = data['instrumentname']
        dbpos.status = data['status']
        dbpos.expirydate = parse(data['expirydate']) if data['expirydate'] else None
        dbpos.size = data['size']
        dbpos.entrydatetime = parse(data['entrydatetime'])
        dbpos.entryprice = data['entryprice']
        dbpos.stoplossprice = data['stoplossprice']
        dbpos.takeprofitprice = data['takeprofitprice']
        dbpos.exitdatetime = parse(data['exitdatetime']) if data['exitdatetime'] else None
        dbpos.exitprice = data['exitprice']
        dbpos.profit = data['profit']

        session.commit()

        return self._positiontodict(position=dbpos)

    def _positiontodict(self, position: Position) -> dict:
        return {
            "accountid": position.accountid,
            "brokerpositionid": position.brokerpositionid,
            "brokerinstrumentidentifier": position.brokerinstrumentidentifier,
            "instrumentname": position.instrumentname,
            "status": position.status,
            "expirydate": position.expirydate.isoformat() if position.expirydate else None,
            "size": position.size,
            "entrydatetime": position.entrydatetime.isoformat(),
            "entryprice": position.entryprice,
            "stoplossprice": position.stoplossprice,
            "takeprofitprice": position.takeprofitprice,
            "exitdatetime": position.exitdatetime.isoformat() if position.exitdatetime else None,
            "exitprice": position.exitprice,
            "profit": position.profit
        }
