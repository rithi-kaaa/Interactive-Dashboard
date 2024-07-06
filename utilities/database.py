from sqlalchemy import select, Table, func
import sys
import pytz
import sqlalchemy as db
import utilities.utils as u
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, select, Table
import numpy as np


def getMostRecentUpdatedDT(database, tableName):
    # https://towardsdatascience.com/sqlalchemy-python-tutorial-79a577141a91
    metadata = db.MetaData()
    table = Table(
        tableName,
        metadata,
        autoload=True,
        autoload_with=database
    )
    lastUpdatedCol = select([
        db.func.max(table.columns.lastupdated)
    ])
    connection = database.connect()
    latestDate = connection.execute(lastUpdatedCol).fetchall()[0][0]

    if latestDate is None:
        return None
    else:
        return str(latestDate)

def checkEpochIsInLastupdated(database, tableName, epoch):
    lastupdate = u.convertEpochToUTCDT(int(epoch/1000))
    conn=database.connect()
    output = conn.execute("SELECT id FROM %s WHERE lastupdated='%s'"%(tableName,lastupdate))
    alloutput =output.fetchall()
    return len(alloutput)!=0

def getSQLRecords(database, tablename, startLastupdated, endLastupdated):
    recordsDF = pd.read_sql_query("SELECT * FROM %s WHERE lastupdated>='%s' AND lastupdated<='%s' " % (
                                           tablename, startLastupdated, endLastupdated),database.connect())
    uniqueLastupdatedCount = len(pd.unique(recordsDF["lastupdated"]))
    eligbleHoursCount = u.getDistinctHoursCountInBetweenDates(startLastupdated, endLastupdated)+1 # include starting hours also
    return recordsDF, uniqueLastupdatedCount==eligbleHoursCount


def getMmmTradesByTs(database, tablename, modelid, exchange, frEpoch, toEpoch):
    with database.connect() as conn:
        if exchange=="":
            tradesRecordsDF = pd.read_sql_query("SELECT * FROM %s WHERE modelid='%s' AND match_ts>=%d AND match_ts<%d" % (
                    tablename, modelid, frEpoch, toEpoch), conn)
        else:
            tradesRecordsDF = pd.read_sql_query("SELECT * FROM %s WHERE modelid='%s' AND match_exch='%s' AND match_ts>=%d AND match_ts<%d" % (
                                                   tablename, modelid, exchange, frEpoch, toEpoch),conn)
    cols = ["id","modelid","seq","match_exch","match_symb","match_fee",
            "match_ts","match_orderid","match_side","match_qty","match_price","match_feeccy"]
    return tradesRecordsDF[cols]

def getMmmPortfoliosBySeq(database, tablename, modelid, seq):
    portfoliosRecordsDF = pd.read_sql_query("SELECT * FROM %s WHERE modelid='%s' AND seq=%d"%(tablename, modelid, seq),database.connect())
    cols = ["id","modelid","seq","match_ts","portfolio"]
    return portfoliosRecordsDF[cols]











