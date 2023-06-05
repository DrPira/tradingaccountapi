from typing import List
from db.models import AccountValue, AccountTransaction
from db.db import Session
import pandas as pd
import numpy as np


class PerformanceCalculator:
    """
    This class is responsible for calculating the performance of a list of accountvalues.
    The list can contain multiple records for the same date, in those cases this class groups the data by date and
    sums it up before calculating performance. This class also fetches transactions during the time range to
    calculate the performance.
    """
    @classmethod
    def calculateperformancefromaccountvalues(cls,
                                              session: Session,
                                              accountvalues: List[AccountValue]) -> pd.DataFrame:
        """
        Calculates performance from a list of accountvalues.
        :param session:
        :param accountvalues:
        :return:
        """
        if not accountvalues:
            return pd.DataFrame()

        df = pd.DataFrame([x.__dict__ for x in accountvalues])
        df = df.groupby('valuedate').sum()
        df['performance'] = 0.0
        df['priorvalue'] = 0.0
        df['sumoftransactions'] = 0.0
        df['priorvalue'] = df['value'].shift(1).fillna(df['value'])

        accounts = set(x.accountdbid for x in accountvalues)

        transactions = AccountTransaction.gettransactionsforperiod(session=session,
                                                                   startdate=df.index.min(),
                                                                   enddate=df.index.max(),
                                                                   accountids=list(accounts))
        df['transactionvalue'] = 0
        if transactions:
            transactions = pd.DataFrame({x.transactiondatetime.date(): x.value} for x in transactions if
                                        not x.internaltransaction and
                                        not x.sharedtransaction and
                                        x.includeinperformance).set_index("transactiondatetime")
            df['transactionvalue'] = transactions

        df['dayperformance'] = (df.value - (df.priorvalue + df.transactionvalue)) / (df.priorvalue + df.transactionvalue)
        df['dayperformance'] += 1.0
        # Cumulative product of dayperformance gives the rangeperformance
        df['rangeperformance'] = np.cumprod(df['dayperformance'])

        return df
