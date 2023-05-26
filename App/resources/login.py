from flask_restful import Resource, reqparse
from db.models import User
from flask_jwt_extended import create_access_token
from datetime import timedelta
from resources.helpers import sessionhandler


class UserLogin(Resource):
    @sessionhandler
    def post(self, session):
        parser = reqparse.RequestParser()
        parser.add_argument("username", required=True)
        parser.add_argument("password", required=True)

        data = parser.parse_args()

        # Get user from database
        result = session.query(User).\
            filter(User.username == data['username']).\
            filter(User.isactive == True).\
            all()

        if len(result) == 0:
            return {"message": "Wrong username or password"}, 401

        userobject = result[0]

        # Validate password on user object
        if userobject.verifypassword(data['password']) is False:
            return {"message": "Wrong username or password"}, 401

        # Generate tokens
        returndict = dict()
        returndict['accesstoken'] = create_access_token(identity=userobject.id, expires_delta=timedelta(minutes=15))

        return returndict
