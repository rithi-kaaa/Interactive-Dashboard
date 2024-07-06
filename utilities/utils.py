import pandas as pd
from datetime import timedelta, timezone, date, datetime
import pytz
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta, MO
import os
import numpy as np
import json
import time
from itertools import groupby

def convert_to_epoch(date="2023-03-01", time="08:00"):
    epoch = pd.to_datetime(date + " " + time)
    epoch = (epoch - dt(1970,1,1)).total_seconds()
    epoch = int(epoch) * 1000
    return epoch

def getDeltaDate(dayNo=0):
    now = dt.utcnow().date()
    return now + timedelta(days=dayNo)

def getDeltaDateFromDate(date, dayNo=0): #date format: 2023-04-02
    y = int(date.split("-")[0])
    m = int(date.split("-")[1])
    d = int(date.split("-")[2])
    dateObj = dt(y,m,d)
    return dateObj+ timedelta(days=dayNo)

def getStdCutoffDate(cutoffHr=8):
    now = dt.now(tz=pytz.UTC)
    if now.hour>=cutoffHr:
        return str(now.date())
    else:
        return str((now + timedelta(days=-1)).date()) # if now is 5/4 before 08:00GMT then consider stopdate is 3/4 because 4/4 pnl not closing yet

def getNowUtcHour():
    now = dt.now(tz=pytz.UTC)
    return int(now.hour)

def getNowUtcDate():
    now = dt.now(tz=pytz.UTC)
    return str(now.date())

def getNowUtcIsoWeekday(): #monday is 1 for isoweekday
    now = dt.now(tz=pytz.UTC)
    return int(now.isoweekday())

def firstDateGreaterThanSecondDate(firstDate, secondDate):
    firstDate = dt.strptime(firstDate, "%Y-%m-%d")
    secondDate = dt.strptime(secondDate, "%Y-%m-%d")
    return firstDate>secondDate

def getDateRangeEpoch(firstDate, secondDate):
    dateRangeEpoch = []
    firstDateEpoch = convert_to_epoch(date=firstDate, time="00:00")
    secondDateEpoch = convert_to_epoch(date=secondDate, time="00:00")
    while(firstDateEpoch<=secondDateEpoch):
        dateRangeEpoch.append(firstDateEpoch)
        firstDateEpoch+=60*60*24*1000
    return dateRangeEpoch

def getDateRange(firstDate, secondDate):
    dateRange= []
    firstDate = dt.strptime(firstDate, "%Y-%m-%d")
    secondDate = dt.strptime(secondDate, "%Y-%m-%d")
    while(firstDate<=secondDate):
        firstDateStr = str(firstDate.date())
        dateRange.append(firstDateStr)
        firstDate += timedelta(days=1)
    return dateRange

def getCurrentDTStr():
    now = dt.now()
    dt_string = now.strftime("%d/%m %H:%M")
    return dt_string

# return example: ('2023-05-22 04:00:00', '2023-05-22 05:00:00')
def getCrtAndPreHrsDTStart():  # dt is datetime object
    now = dt.now(tz=pytz.UTC)
    nowDTHrStart = str(now.date())+" "+str(now.time()).split(":")[0] + ":00:00"
    nowM1Hr =  now + timedelta(hours=-1)
    nowDTM1HrStart = str(nowM1Hr.date())+" "+str(nowM1Hr .time()).split(":")[0] + ":00:00"
    return nowDTM1HrStart, nowDTHrStart

def getHalfDayReportingDT():  # dt is datetime object
    now = dt.now(tz=pytz.UTC)
    nowDTFr = str(now.date())+" 00:00:00"
    nowDTTo = str(now.date()) + " 09:00:00"
    return nowDTFr, nowDTTo

def getNextHrStartEpoch():  # dt is datetime object
    now = dt.now(tz=pytz.UTC)
    nowP1DT =  now + timedelta(hours=1)
    nowP1HrStart = str(nowP1DT.date())+" "+str(nowP1DT.time()).split(":")[0] + ":00:00"
    nowP1HrStartEpoch = convert_to_epoch(date=nowP1HrStart.split(" ")[0], time=nowP1HrStart.split(" ")[1])
    return nowP1HrStartEpoch

def getWeeklyReportingDts(): #will return [frEpoch,toEpoch] * 7 days combination
    Dts=[]
    todayDate = date.today()
    lastMonday = todayDate + relativedelta(weekday=MO(-1))
    dayEndEpoch = convert_to_epoch(str(lastMonday),"00:00")
    for i in range(7):
        Dts.append([dayEndEpoch-(60*60*1000*24*(i+1)),dayEndEpoch-(60*60*1000*24*i)])
    return Dts

def deleteFile(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        print("The file does not exist")

def getMinMaxFromDts(dts):
    dts = np.array(dts).flatten()
    return dts.min(), dts.max()

#getDictKeyFromValue(perpModels,"604ca814de")
def getDictKeyFromValueList(my_dict, value, elementNo=0):
    for k in my_dict.keys():
        if my_dict[k][elementNo]==value:
            return k
    return None


def getSecondValueAsList(my_dict):
    my_values = list(my_dict.values())
    secondValueList = []
    for v in my_values:
        secondValueList.append(v[1])
    return secondValueList

def convertEpochToUTCDT(epoch):
    datetime_obj = datetime.fromtimestamp(epoch, timezone.utc)
    return (str(datetime_obj.strftime("%Y-%m-%d %H:%M:%S")))

def getLatestHourAndDaysAgoUTCDT(dayNo):
    now = dt.now(tz=pytz.UTC)
    latestDT = str(now).split(":")[0] + ":00:00"
    weekAgoNow = now-timedelta(days=dayNo)
    weekAgoDT = str(weekAgoNow).split(":")[0] + ":00:00"
    return weekAgoDT, latestDT

def getDistinctHoursCountInBetweenDates(startDT, endDT):
    startD = startDT.split(" ")[0]
    startT = startDT.split(" ")[1]
    startEpoch = convert_to_epoch(startD, startT)

    endD = endDT.split(" ")[0]
    endT = endDT.split(" ")[1]
    endEpoch = convert_to_epoch(endD, endT)

    totalHours = int((endEpoch-startEpoch)/(60*60*1000))
    return totalHours

def getNowUtcDateTime():
    nowUTC = dt.now(tz=pytz.UTC)
    nowUTC = nowUTC.strftime("%Y-%m-%d %H:%M:%S")
    return nowUTC

#getDictKeyFromSubkeyAndValue(spotModels,"bit","BTC-USDT")
def getDictKeyFromSubkeyAndValue(my_dict, subkey, value):
    #return first found key
    for k in my_dict.keys():
        try:
            if my_dict[k][subkey] == value:
                return k
            else:
                continue
        except:
            continue
    return None

def getAllSubKeyValues(my_dict, subkey):
    values = []
    #return first found key
    for k in my_dict.keys():
        try:
            values.append(my_dict[k][subkey])
        except:
            continue
    return values

def getValueFromJsonStr(jsonStr, key, subkey):
    myDict = json.loads(jsonStr)
    return myDict[key][subkey]

def replaceValueInDictStr(myDictStr, key, valueToReplaceInDict):
    myDict = json.loads(myDictStr)
    myDict[key] = valueToReplaceInDict
    return json.dumps(myDict)


def getCurrentEpoch():
    return int(time.time()*1000)

def createDictFromDF(df, keyColumn, valueColumn):
    dfDict = {}
    for index, row in df.iterrows():
        dfDict[row[keyColumn]]=row[valueColumn]
    return dfDict

def getEpochUTCHour(epoch):
    _epoch = int(epoch/1000)
    datetime_obj = datetime.fromtimestamp(_epoch, timezone.utc)
    return int(datetime_obj.hour)

def splitList(origList,chunksize):
    n= chunksize
    l = origList
    splittedList = [l[i:i + n] for i in range(0, len(l), n)]
    return splittedList

def split_text(s):
    for k, g in groupby(s, str.isalpha):
        yield ''.join(g)














