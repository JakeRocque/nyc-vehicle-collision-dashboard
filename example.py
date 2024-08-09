import os
import pandas as pd
import requests

API_KEY = ['speh9fBslbzDZwPgw4Xsyv6il']

COLUMNS = ['ZIPCODE', 'INCIDENT_RESPONSE_SECONDS_QY', 'INCIDENT_DATETIME']

def get_ems_data(key, limit, year1, year2, columns):
    '''retreives EMS data for the city of new york according to specified parameters
       requires an API key, input for how many values should be generated,
       a starting year, and ending year, and a list of columns from the API to generate
    '''
    url = 'https://data.cityofnewyork.us/resource/76xm-jjuj.json'

    select_columns = ",".join(columns)

    where_condition = f"INCIDENT_DATETIME >= '{year1}-01-01T00:00:00.000' AND INCIDENT_DATETIME <= '{year2}-12-31T23:59:59.999'"

    params = {'$$app_token': key,
              'VALID_INCIDENT_RSPNS_TIME_INDC': 'Y',
              '$where': where_condition,
              '$limit': limit,
              '$select': select_columns}

    response = requests.get(url, params=params)
    data = response.json()
    return data

print(get_ems_data('speh9fBslbzDZwPgw4Xsyv6il', 50, 2015, 2022, COLUMNS))