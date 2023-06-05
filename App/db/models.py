from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Column, ForeignKey, Boolean, Float, Date, DateTime, Text, BigInteger
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from passlib.hash import pbkdf2_sha256 as sha256

Base = declarative_base()


class User(Base):
    __tablename__ = 'apiusers'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    password = Column(String(2000), nullable=False)
    isactive = Column(Boolean)
    isadmin = Column(Boolean)

    def verifypassword(self, passwordentered) -> bool:
        return sha256.verify(passwordentered, self.password)


class UserAccountLink(Base):
    __tablename__ = "useraccountlinks"

    """
    A class the represents a database that records the connection between users and accounts. This is used to
    determine which users have access to which accounts.
    """
    id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("apiusers.id"))
    accountid = Column(Integer, ForeignKey("accounts.id"))
    isactive = Column(Boolean, default=True)
    isadmin = Column(Boolean, default=False)
    isowner = Column(Boolean, default=False)
    isreadonly = Column(Boolean, default=False)
    isreadwrite = Column(Boolean, default=False)
    isreadtrading = Column(Boolean, default=False)
    isreadtransactions = Column(Boolean, default=False)
    isreadpositions = Column(Boolean, default=False)
    isreadorders = Column(Boolean, default=False)
    isreadbalances = Column(Boolean, default=False)
    isreadtrades = Column(Boolean, default=False)

    @staticmethod
    def getlinksforuser(session: Session, userid: int) -> List['UserAccountLink']:
        return session.query(UserAccountLink).filter(UserAccountLink.userid == userid).all()


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)
    startdate = Column(Date)

    @staticmethod
    def getstrategiesforuser(session: Session, userid: int) -> List['Strategy']:
        return session.query(Strategy).\
            join(StrategyUserLink).\
            filter(StrategyUserLink.userid == userid).\
            filter(StrategyUserLink.isactive == True).all()

    @staticmethod
    def getstrategywithname(session: Session, name: str) -> 'Strategy':
        return session.query(Strategy).filter(Strategy.name == name).first()

    @staticmethod
    def getallstrategies(session: Session) -> List['Strategy']:
        return session.query(Strategy).all()

    @staticmethod
    def getstrategywithid(session: Session, id: int) -> 'Strategy':
        return session.query(Strategy).filter(Strategy.id == id).first()

    @staticmethod
    def canuserusestrategy(session: Session, userid: int, strategyid: int) -> bool:
        link = session.query(StrategyUserLink).filter(StrategyUserLink.userid == userid).\
            filter(StrategyUserLink.strategyid == strategyid).first()
        return link.isactive

    @staticmethod
    def canusereditstrategy(session: Session, userid: int, strategyid: int) -> bool:
        link = session.query(StrategyUserLink).filter(StrategyUserLink.userid == userid).\
            filter(StrategyUserLink.strategyid == strategyid).first()
        return link.isactive and (link.isadmin or link.isowner)


class StrategyUserLink(Base):
    """
    A class that represents a database that records the connection between users and strategies. This is used to
    determine which users have access to which strategies.
    """
    __tablename__ = "strategyuserlinks"

    id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("apiusers.id"))
    strategyid = Column(Integer, ForeignKey("strategies.id"))
    isactive = Column(Boolean, default=True)
    isadmin = Column(Boolean, default=False)
    isowner = Column(Boolean, default=False)
    isreadonly = Column(Boolean, default=False)
    isreadwrite = Column(Boolean, default=False)


class Account(Base):
    """
    This class represents a trading account. It is used to store the account id and the strategy that is currently
    executing on the account.
    """
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    accountid = Column(Text, nullable=False)
    name = Column(Text)
    currency = Column(String(3))
    timezone = Column(String(100))
    executingstrategy = Column(Integer, ForeignKey("strategies.id"))
    isactive = Column(Boolean, default=True)
    lasttradeupdate = Column(DateTime)
    lasttransactionupdate = Column(DateTime)

    @staticmethod
    def getactiveaccounts(session: Session) -> List['Account']:
        return session.query(Account).filter(Account.isactive == True).all()

    @staticmethod
    def getaccountbyaccountid(session: Session, accountid: str) -> 'Account':
        account = session.query(Account).filter(Account.accountid == accountid).first()
        if account is None:
            account = Account(accountid=accountid)
            session.add(account)
            session.flush([account])
        return account

    @staticmethod
    def getaccountsbyuserid(session: Session, userid: int) -> List['Account']:
        links = session.query(UserAccountLink).filter(UserAccountLink.userid == userid).all()
        accountids = [link.accountid for link in links]
        return session.query(Account).filter(Account.id.in_(accountids)).all()

    @staticmethod
    def canusereditaccount(session: Session, userid: int, accountid: int) -> bool:
        link = session.query(UserAccountLink).filter(UserAccountLink.userid == userid).\
            filter(UserAccountLink.accountid == accountid).first()
        return link.isadmin or link.isowner or link.isreadwrite


class AccountValue(Base):
    __tablename__ = "accountvalue"

    id = Column(Integer, primary_key=True)
    accountdbid = Column(Integer, ForeignKey("accounts.id"), index=True)
    valuedate = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    executedstrategyid = Column(Integer, ForeignKey("strategies.id"), index=True)

    @staticmethod
    def getdbobjvalueforidanddate(session: Session, valuedate: date, accountdbid: int) -> 'AccountValue':
        existing = session.query(AccountValue). \
            filter(AccountValue.valuedate == valuedate). \
            filter(AccountValue.accountdbid == accountdbid).first()
        if existing is None:
            existing = AccountValue(valuedate=valuedate)
            existing.valuedate = valuedate
            existing.accountdbid = accountdbid
            session.add(existing)
        return existing

    @staticmethod
    def getaccountvalueforperiod(session: Session,
                                 accountid: int,
                                 startdate: date,
                                 enddate: date) -> List['AccountValue']:
        return session.query(AccountValue).\
            filter(AccountValue.valuedate >= startdate).\
            filter(AccountValue.valuedate <= enddate).\
            filter(AccountValue.accountdbid == accountid).all()

    @staticmethod
    def getaccountvaluesforstrategy(session: Session, strategyid: int) -> List['AccountValue']:
        return session.query(AccountValue).filter(AccountValue.executedstrategyid == strategyid).all()


class PortfolioValue(Base):
    __tablename__ = "portfoliovalue"

    id = Column(Integer, primary_key=True)
    valuedate = Column(Date, nullable=False)
    totalvalue = Column(Float, nullable=False)
    performance = Column(Float)
    shareprice = Column(Float)

    @staticmethod
    def setaccountvaluefordate(session: Session, valuedate: date, totalvalue: float):
        existing = session.query(PortfolioValue).filter(PortfolioValue.valuedate == valuedate).first()
        if existing is None:
            existing = PortfolioValue(valuedate=valuedate)
            existing.valuedate = valuedate
            session.add(existing)
        existing.totalvalue = totalvalue

    @staticmethod
    def getaccountvalueforperiod(session: Session, startdate: date, enddate: date) -> List['PortfolioValue']:
        return session.query(PortfolioValue).\
            filter(PortfolioValue.valuedate >= startdate).\
            filter(PortfolioValue.valuedate <= enddate).all()

    @staticmethod
    def getvaluefordate(session: Session, valuedate: date) -> 'PortfolioValue':
        dbobj = session.query(PortfolioValue).filter(PortfolioValue.valuedate == valuedate).first()
        if not dbobj:
            dbobj = PortfolioValue(valuedate=valuedate, totalvalue=0.0)
            session.add(dbobj)
        return dbobj


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    accountid = Column(Integer, ForeignKey("accounts.id"), index=True)
    brokerpositionid = Column(String(200), index=True, nullable=False)
    brokerinstrumentidentifier = Column(Text)
    instrumentname = Column(String(50))
    status = Column(String(25))
    expirydate = Column(DateTime)
    size = Column(Float)
    entrydatetime = Column(DateTime)
    entryprice = Column(Float)
    stoplossprice = Column(Float)
    takeprofitprice = Column(Float)
    exitdatetime = Column(DateTime)
    exitprice = Column(Float)
    profit = Column(Float)

    @staticmethod
    def getdbpositionfordealid(session: Session, dealid: str) -> 'Position':
        return session.query(Position).filter(Position.dealid == dealid).first()

    @staticmethod
    def getdbpositionfordbid(session: Session, dbid: int) -> 'Position':
        return session.query(Position).filter(Position.id == dbid).first()


class AccountTransaction(Base):
    __tablename__ = "accounttransactions"

    id = Column(Integer, primary_key=True)
    accountdbid = Column(Integer, ForeignKey('accounts.id'))
    brokertransactionid = Column(BigInteger)
    transactiondatetime = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    investor = Column(Integer, ForeignKey('investors.id'))
    sharestraded = Column(Float)
    sharedtransaction = Column(Boolean, default=False)
    internaltransaction = Column(Boolean, default=False)
    includeinperformance = Column(Boolean, default=False)

    @staticmethod
    def puttransaction(session: Session,
                       igtransactionid: int,
                       transactiondate: date,
                       value: float,
                       accountid: str) -> 'AccountTransaction':
        existing = session.query(AccountTransaction).\
            filter(AccountTransaction.igtransactionid == igtransactionid).\
            filter(AccountTransaction.accountid == accountid).first()
        if existing is None:
            existing = AccountTransaction(igtransactionid=igtransactionid,
                                          transactiondate=transactiondate,
                                          value=value,
                                          accountid=accountid,
                                          includeinperformance=True)
            session.add(existing)
        existing.value = value
        existing.transactiondate = transactiondate

        return existing

    @staticmethod
    def gettransactionsforperiod(session: Session,
                                 startdate: date,
                                 enddate: date,
                                 accountids: Optional[List[int]]) -> List['AccountTransaction']:
        if not accountids:
            return session.query(AccountTransaction). \
                filter(AccountTransaction.transactiondate >= startdate). \
                filter(AccountTransaction.transactiondate <= enddate).all()
        return session.query(AccountTransaction). \
            filter(AccountTransaction.transactiondatetime >= startdate). \
            filter(AccountTransaction.transactiondatetime <= enddate). \
            filter(AccountTransaction.accountdbid.in_(accountids)).all()

    @staticmethod
    def gettransactionsbyinvestor(session: Session, investorid: int) -> List['AccountTransaction']:
        return session.query(AccountTransaction).\
            filter(AccountTransaction.investor == investorid).\
            order_by(AccountTransaction.transactiondatetime.desc()).all()


class Investor(Base):
    __tablename__ = "investors"

    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200))
    noofshares = Column(Float)
    averageacquisitioncost = Column(Float)
    netassetvalue = Column(Float)

    @staticmethod
    def getallinvestors(session: Session) -> List['Investor']:
        return session.query(Investor).all()
