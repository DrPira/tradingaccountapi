from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask import g
from flask import request
import os
import logging
from time import time

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ['JWTSecret']
jwt = JWTManager(app)

api = Api(app)

@app.before_request
def beforereq():
    g.start = time()
    logging.debug(f"{request.method} {request.endpoint} started")


@app.after_request
def afterreq(response):
    diff = time() - g.start

    logging.debug(f"{request.method} {request.endpoint} took: {diff} seconds")

    return response


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.info')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

