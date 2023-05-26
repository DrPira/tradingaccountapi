from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.dbconfig import mysqlusername, mysqlpassword, mysqlhost, mysqldatabase
from db.models import Base
import os

echo = os.environ.get("DEBUG", "") == "True"

engine = create_engine('mysql+mysqlconnector://{}:{}@{}/{}'.format(
    mysqlusername,
    mysqlpassword,
    mysqlhost,
    mysqldatabase), echo=echo, pool_recycle=360, pool_size=5, max_overflow=40)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine, expire_on_commit=False)

readonlysession = sessionmaker(bind=engine, autocommit=True)
