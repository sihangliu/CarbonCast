# script copied from entsoeParser.py in chae_reu branch then modified
import os
import requests
import pandas as pd
from entsoe import EntsoePandasClient
from datetime import datetime, timedelta
import time
import sys
import numpy as np

# public key for ENTSOE API
ENTSOE_API_KEY="c0b15cbf-634c-4884-b784-5b463182cc97"

# Referring ElectricityMap for grouping ENTSOE sources into used sources
#(Eg., nat_gas = fossil coal derived gas + fossil gas)
# Refer this: https://github.com/electricitymaps/electricitymaps-contrib/blob/master/parsers/ENTSOE.py

# Converting to common names as in eiaParser.py
ENTSOE_SOURCES = {
    "Solar": "SOL",
    "Wind Offshore": "WND",
    "Wind Onshore": "WND"
}

# map ENTSOE fuel types to source types
ENTSOE_SOURCE_MAP = {
    "SOL": "solar",
    "WND": "wind"
    }

ENTSOE_BAL_AUTH_LIST = ['AL', 'AT', 'BE', 'BG', 'HR', 'CZ', 'DK', 'DK-DK2', 'EE', 'FI', 
                         'FR', 'DE', 'GB', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'NL',
                        'PL', 'PT', 'RO', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH']
INVALID_AUTH_LIST = ['AL', 'DK-DK2']

# get forecast data by source type from ENTSOE API
def getSolarWindForecastBySourceTypeFromENTSOE(ba, curDate, curEndDate):
    print(ba)

    startDate = pd.Timestamp(curDate, tz='UTC')
    endDate = pd.Timestamp(curEndDate, tz='UTC') + pd.Timedelta(hours=23, minutes=45) # FIX; appropriate end time

    print(startDate, endDate)

    client = EntsoePandasClient(api_key=ENTSOE_API_KEY)

    try:
        dataset = client.query_wind_and_solar_forecast(ba, start=startDate, end=endDate, psr_type=None)
        empty = False
    except: # try to do only NoMatchingDataError
        # fillEmptyData(startDate, pd.Timestamp(curEndDate, tz='UTC'))
        dataset = pd.DataFrame()
        empty = True

    return dataset, empty

# parse forecast data by source type from ENTSOE API
def parseENTSOESolarWindForecastBySourceType(data, startDate, ForecastSources, numSources, numDays):   
    solarWindForecastBySource = {}
    hourlyForecastData = []
    solarWindForecastData = []

    if (len(data) == 0):
        # empty data fetched from ENTSOE. For now, make everything Nan
        for hour in range(24 * numDays): # figure out DAY_JUMP thing
            tempHour = startDate + timedelta(hours=hour)
            hourlyForecastData = [tempHour.strftime("%Y/%m/%d %H:00")]
            for j in range(numSources):
                hourlyForecastData.append(np.nan)
            solarWindForecastData.append(hourlyForecastData)
        datasetColumns = ["UTC time"]
        for source in ForecastSources:
            datasetColumns.append(source)

        # print(solarWindForecastData)
        dataset = pd.DataFrame(solarWindForecastData, columns=datasetColumns)

        return dataset, dataset

    curDate = data.index[0].astimezone(tz='UTC').strftime("%Y-%m-%d %H:%M")
    #curDate = curTime.strftime("%Y-%m-%d") # above used to be curTime

    # checking if time starts from 00:00
    curHour = data.index[0].astimezone(tz='UTC').hour
    for hour in range(int(curHour)): 
        hourlyForecastData = [curDate.split(" ")[0]+" "+str(hour).zfill(2)+":00"]
        for j in range(numSources):
            hourlyForecastData.append(np.nan)
        solarWindForecastData.append(hourlyForecastData)
    hourlyForecastData = []
    hourlyForecastData.append(curDate)

    # include a function adding up 15-min interval data to an hour; assuming only 1hr & 15min intervals in data
    if (data.index[1].minute == 15):
        print("15 minutes intervals")
        data = adjustMinIntervalData(data, interval=15)
    elif (data.index[1].minute == 30):
        print("30 minutes intervals")
        data = adjustMinIntervalData(data, interval=30)
    elif (data.index[1].minute == 0):
        print("hour intervals")
    else: # safety code for detecting intervals other than 1hr or 15min
        print("some other interval")
        exit(0)
    # debug from here and on; for non-hourly intervals, there's an error
    
    for row in range(len(data)):
        time = data.index[row].astimezone(tz='UTC').strftime("%Y-%m-%d %H:%M")
        # iterate through each entry in the row
        for column in range(len(data.columns)):
            # find which source
            colVal = data.columns[column]
            if (type(colVal) is tuple):
                colVal = colVal[0]
            sourceKey = ENTSOE_SOURCES[colVal]
            source = ENTSOE_SOURCE_MAP[sourceKey]
            if (source not in solarWindForecastBySource.keys()):
                solarWindForecastBySource[source] = 0 

            if (time == curDate):
                solarWindForecastBySource[source] = solarWindForecastBySource[source] + data.iloc[row][column]
            else: # entered when time ahead of curDate; new time/row
                curDate = time
                for src in ForecastSources:
                    if (src not in solarWindForecastBySource.keys()): # if was not already filled at the previous time
                        solarWindForecastBySource[src] = np.nan 
                    hourlyForecastData.append(solarWindForecastBySource[src]) 
                solarWindForecastData.append(hourlyForecastData) # adding previous hour's data
                hourlyForecastData = [curDate] # adding the current time
                solarWindForecastBySource = {} # reset?
                solarWindForecastBySource[source] = data.iloc[row][column]

    for source in ForecastSources: # for the last iteration of row
        if (source not in solarWindForecastBySource.keys()): # if was not already filled at the previous time
            solarWindForecastBySource[source] = np.nan
        hourlyForecastData.append(solarWindForecastBySource[source])
    solarWindForecastData.append(hourlyForecastData)
    
    # filling in missing timestamps/indeces
    if (len(solarWindForecastData) < (24 * numDays)):
        curDate = datetime.strptime(curDate, "%Y-%m-%d %H:%M")
        for hour in range(len(solarWindForecastData), (24 * numDays)):
            curDate = curDate + timedelta(hours=1)
            hourlyForecastData = [curDate.strftime("%Y-%m-%d %H:%M")]
            for source in range(numSources):
                hourlyForecastData.append(np.nan)
            solarWindForecastData.append(hourlyForecastData)

    datasetColumns = ["UTC time"]
    for source in ForecastSources:
        datasetColumns.append(source)

    dataset = pd.DataFrame(solarWindForecastData, columns=datasetColumns)

    return data, dataset

def getSolarWindForecastFromENTSOE(balAuth, startDate, numDays, DAY_JUMP):
    
    fullDataset = pd.DataFrame() # where to save the whole dataset
    startDateObj = datetime.strptime(startDate, "%Y-%m-%d") # input date converted to yyyy-mm-dd format
    ForecastSources = set() # for the loop
    numSources = 0 # for the loop

    print("start date:", startDate)

    for days in range(0, numDays, DAY_JUMP): # DAY_JUMP: # days of data got each time
        endDateObj = startDateObj + timedelta(days=DAY_JUMP-1)
        endDate = endDateObj.strftime("%Y-%m-%d")
        data, empty = getSolarWindForecastBySourceTypeFromENTSOE(balAuth, startDate, endDate)
        print("was the dataset empty?: ", empty)

        if (empty):
            numSources = 2
            ForecastSources = ["solar", "wind"]
        elif (numSources <= 2): # only run the for-loop if there might be new sources added to the list
            for i in range(len(data.columns.values)):
                colVal = data.columns.values[i]
                if (type(colVal) is tuple):
                    colVal = colVal[0]
                sourceKey = ENTSOE_SOURCES[colVal]
                source = ENTSOE_SOURCE_MAP[sourceKey]
                ForecastSources.add(source)
            numSources = len(ForecastSources)

        hourlyData, dataset = parseENTSOESolarWindForecastBySourceType(data, startDateObj, ForecastSources, numSources, DAY_JUMP)

        if (days == 0):
            fullDataset = dataset.copy()
            fullRawData = data.copy()
            fullHourly = hourlyData.copy()
        else:
            if (days%60 == 0):
                time.sleep(1)
            fullDataset = pd.concat([fullDataset, dataset])
            fullRawData = pd.concat([fullRawData, data])
            fullHourly = pd.concat([fullHourly, hourlyData])

        # startDate incremented    
        startDateObj = startDateObj + timedelta(days=DAY_JUMP)
        startDate = startDateObj.strftime("%Y-%m-%d")

        # print(fullDataset.tail(2))
    return fullRawData, fullHourly, fullDataset

# def concatDataset():
#     # fix directories later when in use
#     for balAuth in ENTSOE_BAL_AUTH_LIST:
#         d1 = pd.read_csv("./eiaData/2019-2021/"+balAuth+".csv", header=0)
#         d2 = pd.read_csv("./eiaData/2022/"+balAuth+".csv", header=0)
#         fullDataset = pd.concat([d1, d2])
#         fullDataset.to_csv("./eiaData/"+balAuth+".csv")
#     return

def cleanSolarWindForecastDataFromENTSOE(dataset, balAuth):
    dataset = dataset.astype(np.float64) # converting type of data to float64
    dataset[dataset<0] = 0 # converting negative numbers to 0; not sure why necessary
    for i in range(len(dataset)):
        for j in range(len(dataset.columns)): # for each entry
            if (pd.isna(dataset.iloc[i,j]) is True or dataset.iloc[i,j] == np.nan): # if values missing
                prevHour = dataset.iloc[i-1, j] if (i-1)>=0 else np.nan # get values from previous & next hour/day
                prevDay = dataset.iloc[i-24, j] if (i-24)>=0 else np.nan
                nextHour = dataset.iloc[i+1, j] if (i+1)<len(dataset) else np.nan
                nextDay = dataset.iloc[i+24, j] if (i+24)<len(dataset) else np.nan
                numerator = 0
                denominator = 0
                if (pd.isna(prevHour) is False): # fill the dates with close hours/days (taking average)
                    numerator += prevHour
                    denominator+=1
                if (pd.isna(prevDay) is False):
                    numerator += prevDay
                    denominator+=1
                if (pd.isna(nextHour) is False):
                    numerator += nextHour
                    denominator+=1
                if (pd.isna(nextDay) is False):
                    numerator += nextDay
                    denominator+=1
                dataset.iloc[i, j] = (numerator/denominator) if denominator>0 else 0 # if no data found, just set to 0
                # print(balAuth, dataset.index.values[i], prevHour, prevDay, nextHour, nextDay, dataset.iloc[i, j])
                # filling missing values by taking average of prevHour, prevDay same hour, 
                # nextHour & nextDay same hour

    # print(balAuth)
    # print(dataset.head())
    return dataset

def adjustColumns(dataset, balAuth):
    sources = ["solar", "wind"]
    modifiedSources = []
    print(dataset.shape)
    modifiedDataset = np.zeros(dataset.shape) # return a new array of the input shape
    idx = 0
    for source in sources:
        if (source in dataset.columns): # create columns for new dataset
            modifiedSources.append(source)
            val = dataset[source].values # get all values from old dataset
            modifiedDataset[:, idx] = val # all rows of 0th column (initially) iterated
            idx += 1
    print(modifiedSources)
    modifiedDataset = pd.DataFrame(modifiedDataset, columns=modifiedSources, index=dataset.index)
    print(modifiedDataset.shape)
    return modifiedDataset

def adjustMinIntervalData(data, interval): # input = pandas dataframe
    newDataframe = pd.DataFrame(columns=data.columns)
    newIndeces = []

    for column in range(len(data.columns)):
        modifiedValues = [] # contains for each column
        for row in range(len(data)):
            if (data.index[row].minute == 0): # new hour started
                if (row != 0):
                    if (interval == 15 and i < 4): # add missing values (previous time block)
                        newValue = (newValue / i) * 4
                    elif (interval == 30 and i < 2):
                        newValue = (newValue / i) * 2
                    modifiedValues.append(newValue) # append old value for previous hour
                if (column == 0):
                    newIndeces.append(data.index[row])
                newValue = data.iloc[row][column]
                i = 1
            else:
                newValue = newValue + data.iloc[row][column]
                i = i + 1

        # for the last row
        if (interval == 15 and i < 4): # add missing values (previous time block)
            newValue = (newValue / i) * 4
        elif (interval == 30 and i < 2):
            newValue = (newValue / i) * 2
        modifiedValues.append(newValue) # append old value for previous hour
        if (column == 0):
            newIndeces.append(data.index[row])
        newDataframe[data.columns.values[column]] = pd.Series(modifiedValues)

    for row in range(len(newDataframe)):
        newDataframe.rename(index={row: newIndeces[row]}, inplace=True)

    return newDataframe

if __name__ == "__main__":
    if (len(sys.argv)!=3):
        print("Usage: python3 entsoeSolarWindForecastParser.py <yyyy-mm-dd> <# days to fetch data for>")
        exit(0)

    startDate = sys.argv[1] # "2022-01-01" #"2019-01-01"
    numDays = int(sys.argv[2]) #368 #1096

    for balAuth in ENTSOE_BAL_AUTH_LIST:
        # fetch forecast data
        rawData, hourlyData, fullDataset = getSolarWindForecastFromENTSOE(balAuth, startDate, numDays, DAY_JUMP=8)
        # DM: For DAY_JUMP > 1, there is a bug while filling missing hours

        # saving files from src folder (should work)
        parentdir = os.path.normpath(os.path.join(os.getcwd(), os.pardir)) # goes to CarbonCast folder
        filedir = os.path.normpath(os.path.join(parentdir, f"./data/EU_DATA/SolarWind/{balAuth}"))
        
        csv_path = os.path.normpath(os.path.join(filedir, f"./{balAuth}_SW_raw.csv"))
        with open(csv_path, 'w') as f: # open as f means opens as file
            rawData.to_csv(f)
    
        csv_path = os.path.normpath(os.path.join(filedir, f"./{balAuth}_SW_hourly.csv"))
        with open(csv_path, 'w') as f: # open as f means opens as file
            hourlyData.to_csv(f)
        
        csv_path = os.path.normpath(os.path.join(filedir, f"./{balAuth}_SW.csv"))
        with open(csv_path, 'w') as f: # open as f means opens as file
            fullDataset.to_csv(f, index=False)
        
        # clean forecast data
        dataset = pd.read_csv(csv_path, header=0, 
                            parse_dates=["UTC time"], index_col=["UTC time"])
        cleanedDataset = cleanSolarWindForecastDataFromENTSOE(dataset, balAuth)
        cleanedDataset.to_csv(filedir+f"/{balAuth}_SW_clean.csv") # see if string suffices

        # adjust source columns
        dataset = pd.read_csv(filedir+f"/{balAuth}_SW_clean.csv", header=0, index_col=["UTC time"])
        modifiedDataset = adjustColumns(dataset, balAuth)
        modifiedDataset.to_csv(filedir+f"/{balAuth}_SW_clean_mod.csv")

        print("reached the end for " + balAuth)

    # concatDataset()