import sys
import os
sys.path.append("/app/trade_capturer/")
from queue import Queue
import platform
import yaml
import queue
import json
import utilities.utils as utils
import utilities.pgdatabase as pgdb
import pandas as pd
from sqlalchemy import create_engine
import time
import _thread
import utilities.slacknotificationmanager as snm
from datetime import datetime

class tradeCapturingSpot():
    def __init__(self, bitConfig, binConfig, slackConfig, dbConfig, mmmSpotModels, spottradestable, reportTo, env):

        self.dbConfig = dbConfig
        user = self.dbConfig["user"]
        pwd = self.dbConfig["pwd"]
        host = self.dbConfig["uri"]
        port = self.dbConfig["port"]
        database = self.dbConfig["dbname"]
        self.i40tradesdb = create_engine('postgresql://%s:%s@%s:%s/%s' % (user, pwd, host, port, database))

        self.spottradestable = spottradestable
        self.binConfig = binConfig
        self.bitConfig = bitConfig
        self.slackConfig = slackConfig
        self.reportTo = reportTo

        self.slacknotifier = snm.slacknotificationmanager("mm_alert", self.slackConfig["mm_alert"])
        print("Start running of WS trade capturing service in %s: %s"%(env,str(datetime.now())))
        self.slacknotifier.slackAlert("Start running of WS trade capturing service in %s: %s"%(env,str(datetime.now())),self.reportTo)  # reporting to testbost channel for service restarting

        self.msgCh  = Queue()
        self.mmmSpotModels = mmmSpotModels
        allBinSpotInsts = utils.getAllSubKeyValues(self.mmmSpotModels, "bin")
        exchLastSpotTradeTimes = pgdb.getTradesMaxTradetimeForExch(self.mmmtradesdb, self.spottradestable)

        #Dangerous: Comment out, used only for first time run
        # if "bin" not in exchLastSpotTradeTimes:exchLastSpotTradeTimes["bin"]=0 # possible with starting without lasttradetime at all
        # if "bit" not in exchLastSpotTradeTimes: exchLastSpotTradeTimes["bit"] = 0

        self.overlappedMsForGapTrades = 1000*60*60*20  #Gaptrades retrieve with overlapped of -20hrs.
        self.checkerCheckingInterval = 1000*60*60*1    #Checker run every1hr.

        self.mmmSpotModels = mmmSpotModels

        self.last25hrsTradeIds = pgdb.getLast25hrsColumnValues(self.mmmtradesdb, self.spottradestable, "trade_id", "event_time")
        self.enforceExitUponEmptyChannelTs = 1000*60*60*0.5 #30mins

    with open(configFilename) as cfgfile:
        config = yaml.load(cfgfile, Loader=yaml.FullLoader)
        if env == "prod":
            bitConfig = config["Bitcom-mmm-spot"]
            binConfig = config["Binance-mmm-spot"]
        elif env == "test":
            bitConfig = config["MMM-SpotPerp-Bit-Test"]
            binConfig = config["MMM-SpotPerp-Bin-Test"]
        else:
            print("Unknown env: %s" % env)
            os._exit(0)

        slackConfig = config["Slack-Client"]
        dbConfig = config["Postgressql-tradingteamservices"]
        tc = tradeCapturingSpot(bitConfig, binConfig, slackConfig, dbConfig, spotModels, spotTradesTable, reportTo, env)
        tc.start()




