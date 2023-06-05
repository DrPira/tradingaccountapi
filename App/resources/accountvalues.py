import datetime
from flask_restful import Resource, reqparse
from db.models import Account, AccountValue
from flask_jwt_extended import get_jwt_identity, jwt_required
from resources.helpers import sessionhandler, useraccountrightsneeded
from dateutil.parser import parse
from dateutil.tz import gettz
from supporting.performancecalculator import PerformanceCalculator


class AccountValues(Resource):
    @jwt_required()
    @sessionhandler
    @useraccountrightsneeded()
    def get(self, session, account):
        parser = reqparse.RequestParser()
        parser.add_argument("startdate", required=False, type=str, location="args")
        parser.add_argument("enddate", required=False, type=str, location="args")

        data = parser.parse_args()

        values = AccountValue.getaccountvalueforperiod(
            session=session,
            accountid=account.id,
            startdate=parse(data['startdate']),
            enddate=parse(data['enddate'])
        )

        df = PerformanceCalculator.calculateperformancefromaccountvalues(session=session, accountvalues=values)
        df = df.reset_index()
        df['valuedate'] = df['valuedate'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df["rangeperformance"] -= 1.0

        return df[["valuedate", "value", "rangeperformance"]].to_dict(orient="records")

    @jwt_required()
    @sessionhandler
    @useraccountrightsneeded(editrights=True)
    def post(self, session, account):
        parser = reqparse.RequestParser()
        parser.add_argument("value", required=True, type=float)

        data = parser.parse_args()

        todayinaccounttimezone = datetime.datetime.now().astimezone(gettz(account.timezone)).date()

        valueobj = AccountValue.getdbobjvalueforidanddate(session=session,
                                                          accountdbid=account.id,
                                                          valuedate=todayinaccounttimezone)
        valueobj.value = data['value']
        valueobj.executedstrategyid = account.executingstrategy

        session.commit()

        return {"message": "Value updated"}, 200
