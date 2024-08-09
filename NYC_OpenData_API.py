import requests
import pandas as pd
from io import StringIO

# defined a class to manage NYC Open Data online API and process queried data
# provides access to up-to-date data as it can access the current state of the online API
class NYCOpenDataAPI:
    def __init__(self, url, key):
        """
        :description: initializes class and sets url and key as class variables
        :param url: given NYC Open Data API url
        :param key: given personal API key
        """

        self.url = url
        self.key = key

    def _fetch_response(self, columns, limit, yr_start, yr_end):
        """
        :param columns: specified columns to pull from the online API
        :param limit: specified limit of how many rows to pull
        :param yr_start: specified start year of requested data
        :param yr_end: specified end year of requested data
        :return: returns the response to the API request as a class variable for future ease of calling
        """

        # join columns as string separated by commas
        if columns:
            columns = ",".join(columns)

        # set where conditions to specify year conditions
        where_condition_year = (f"CRASH_DATE >= '{yr_start}-01-01T00:00:00.000' AND CRASH_DATE <= '{yr_end}"
                                f"-12-31T23:59:59.999'")

        # set where conditions to ensure 'borough' and 'on_street_nme' columns are not null
        where_condition_borough = f"BOROUGH IS NOT NULL"
        where_condition_street = f"ON_STREET_NAME IS NOT NULL"

        params = {'$$app_token': self.key,
                  '$select': columns,
                  '$limit': limit,
                  '$where': f"{where_condition_year} AND {where_condition_borough} AND {where_condition_street}"
                  }

        # attempt to query the API, if unsuccessful print error
        try:

            self.response = requests.get(self.url, params=params)

        except Exception as e:
            print("Error while fetching the response:", e)

    def fetch_data(self, columns=None, limit=1000, yr_start=2000, yr_end=3000):
        """
        :param columns: specified columns to pull from the online API
        :param limit: specified limit of how many rows to pull
        :param yr_start: specified start year of requested data
        :param yr_end: specified end year of requested data
        :return: returns a pandas df from the API based on the specified params
        """

        # call the _fetch_response function to generate a response
        self._fetch_response(columns, limit, yr_start, yr_end)

        # make sure response has been generated and read it into a df using pandas
        if self.response is not None:
            try:
                csv_data = StringIO(self.response.text)  # first, turn data into csv
                df = pd.read_csv(csv_data)
                return df

            # print error if error occurs
            except Exception as e:
                print("Error while parsing CSV data:", e)
                return None

        else:
            print("Response not generated.")
            return None

    @staticmethod
    def process_strings(df):
        """
        :param df: given df with some object type colmns
        :return: returns df with all strings having their whitespace removed and titled
        """

        # iterate over entire df
        for column in df.columns:
            # check for object columns
            if df[column].dtype == 'object':
                # convert strings to lowercase and remove whitespace
                df[column] = df[column].str.title().str.strip()
        return df

    @staticmethod
    def _convert_time_to_range(time):
        """
        :param time: given time to convert into an hourly range
        :return: returns time converted into a string which denotes the hour which the time falls under
        """
        hour, minute = time.split(':')
        start_hour = hour
        end_hour = (int(hour) + 1) % 24
        return f'{start_hour}-{end_hour}'

    @staticmethod
    def convert_time_col_to_ranges(df, col):
        """
        :param df: given df to turn column of times into ranges
        :param col: specified column name for column of times
        :return:
        """

        return df[col].apply(NYCOpenDataAPI._convert_time_to_range)

    @staticmethod
    def fetch_unique_labels(df, col):
        """
        :param df: given df to find unique labels from specified column
        :param col: given column of desired labels
        :return: returns a list every unique element in a column with strings titled
        """

        labels = df[col].unique()

        formatted_labels = [label.title() if isinstance(label, str) else 'None' for label in labels]
        return formatted_labels

    @staticmethod
    def filter_by_year_and_borough(df, yr_start=2012, yr_end=2023, boroughs=None):
        """
        :param df: given df to filter data by year range and specified boroughs
        :param yr_start: start of year range to filter data by
        :param yr_end: end of year range to filter data by
        :param boroughs: specified boroughs to filter data by
        :return: returns df with 'crash_date' and 'borough' column filtered by specified time range and boroughs
        """

        # makes sure values in crash date are pandas date time objects
        df['crash_date'] = pd.to_datetime(df['crash_date'])
        df['crash_year'] = df['crash_date'].dt.year

        # filter df based on the given year range
        df_filtered = df[(df['crash_year'] >= yr_start) & (df['crash_year'] <= yr_end)]

        if boroughs:
            df_filtered = df_filtered[df_filtered['borough'].isin(boroughs)]  # if boroughs are given, filter by them

        return df_filtered
