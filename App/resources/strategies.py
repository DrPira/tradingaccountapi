from flask_restful import Resource, reqparse
from db.models import Strategy, StrategyUserLink
from flask_jwt_extended import get_jwt_identity, jwt_required
from resources.helpers import sessionhandler
from datetime import datetime


class Strategies(Resource):
    @jwt_required()
    @sessionhandler
    def get(self, session):
        strategies = Strategy.getstrategiesforuser(session=session, userid=get_jwt_identity())

        return [self._returndictforstrategy(x) for x in strategies]


    @jwt_required()
    @sessionhandler
    def put(self, session):
        parser = reqparse.RequestParser()
        parser.add_argument("strategyid", required=True)
        parser.add_argument("strategyname", required=False)
        parser.add_argument("description", required=False)

        data = parser.parse_args()

        strtegies = Strategy.getstrategiesforuser(session=session, userid=get_jwt_identity())
        try:
            strategy = next(x for x in strtegies if x.id == int(data['strategyid']))
        except StopIteration:
            return {"message": "Strategy not found"}, 404

        if not Strategy.canusereditstrategy(session=session, userid=get_jwt_identity(), strategyid=strategy.id):
            return {"message": "User cannot edit strategy"}, 401

        if data['strategyname']:
            strategy.name = data['strategyname']

        if data['description']:
            strategy.description = data['description']

        session.commit()

        return self._returndictforstrategy(strategy)

    @jwt_required()
    @sessionhandler
    def post(self, session):
        parser = reqparse.RequestParser()
        parser.add_argument("strategyname", required=True)
        parser.add_argument("description", required=True)

        data = parser.parse_args()

        newstrategy = Strategy()
        newstrategy.name = data['strategyname']
        newstrategy.description = data['description']
        newstrategy.startdate = datetime.now().date()
        session.add(newstrategy)
        session.flush([newstrategy])

        newlink = StrategyUserLink()
        newlink.userid = get_jwt_identity()
        newlink.strategyid = newstrategy.id
        newlink.isowner = True

        session.add(newlink)
        session.commit()

        return self._returndictforstrategy(newstrategy)

    @staticmethod
    def _returndictforstrategy(strategy: Strategy):
        return {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "startdate": strategy.startdate.isoformat()
        }
