import pandas as pd
import NYC_Collision_Dash as nd
from NYC_OpenData_API import NYCOpenDataAPI
from dash import Dash, dcc, html, Input, Output

URL = 'https://data.cityofnewyork.us/resource/h9gi-nx95.csv'
KEY = 'UHuQ1JuV1fHgvlc4eWkFETreT'
COLUMNS = ['crash_date',
           'crash_time',
           'borough',
           'latitude',
           'longitude',
           'on_street_name',
           'contributing_factor_vehicle_1',
           'vehicle_type_code1',
           'number_of_persons_injured',
           'number_of_persons_killed']


def main():
    # initialize the API
    api = NYCOpenDataAPI(URL, KEY)

    # fetch and clean the relevant data
    # depending on computer power, lower limit as needed - put 10 million to include all data
    data = api.fetch_data(columns=COLUMNS, limit=10000000)
    df = api.process_strings(data)  # remove trailing/leading white space and title all strings in df
    # convert specific times to hourly ranges - '3:12' to '3-4'
    df['crash_time'] = api.convert_time_col_to_ranges(df, 'crash_time')
    df['crash_date'] = pd.to_datetime(df['crash_date'])  # turn date ranges to pandas datetime object for processing

    # initialize plotly dashboard
    app = Dash(__name__)

    # set up the layout of all items on the dashboard
    app.layout = html.Div([

        # create and style a centered title on the top of the screen
        html.H1('Motor Vehicle Collisions NYC, By Individual Collision',
                style={'fontFamily': 'Roboto, sans-serif', 'color': 'rgba(113, 156, 170, 0.9)',
                       'text-align': 'center', 'margin-top': '10px'}),

        # create and style a dropdown menu with options defined by all unique boroughs in borough column
        dcc.Dropdown(
            id='borough_dropdown',
            options=api.fetch_unique_labels(df, 'borough'),
            value='Manhattan',  # set Manhattan as the default value
            multi=True,
            style={'fontFamily': 'Roboto, sans-serif', 'color': 'rgba(30, 30, 30, 0.75)',
                   'margin-bottom': '20px'}
        ),

        # create a div for year range label and year range slider
        html.Div([

            # create and style a label for the year range slider
            html.Label('Select Year Range:',
                       style={'fontFamily': 'Roboto, sans-serif',
                              'color': 'rgba(30, 30, 30, 0.75)',
                              'margin-top': '20px'}
                       ),
            # create and style a slider whose values are determined by the min and max year of the crash date column
            dcc.RangeSlider(
                id='year_range_slider',
                min=df['crash_date'].min().year,
                max=df['crash_date'].max().year,
                step=1,

                # set the range of the slider to be the min to the max year with an interval of 1
                marks={year: {'label': str(year), 'style': {'fontFamily': 'Roboto, sans-serif'}} for year in
                       range(df['crash_date'].min().year, df['crash_date'].max().year + 1)},
                value=[2022, 2023],  # set default value to be 2022-2023
            )
        ], style={'text-align': 'center', 'margin-top': '10px'}
        ),

        # create and style a checklist with given columns to determine inputs to sankey diagram
        dcc.Checklist(
            id='sankey_columns_checklist',
            options=[
                {'label': 'Street Name', 'value': 'on_street_name'},
                {'label': 'Contributing Factor', 'value': 'contributing_factor_vehicle_1'},
                {'label': 'Vehicle Type', 'value': 'vehicle_type_code1'},
                {'label': 'Time Of Collision', 'value': 'crash_time'}
            ], value=['contributing_factor_vehicle_1', 'vehicle_type_code1'],  # set default selected columns
            inline=True,
            style={'position': 'absolute', 'left': '75%', 'top': '25%', 'transform': 'translate(-50%, 0%)',
                   'fontFamily': 'Roboto, sans-serif', 'zIndex': '999', 'fontSize': '18px',
                   'whiteSpace': 'nowrap', 'color': 'rgba(30, 30, 30, 0.75)'}
        ),

        # create a div to format and style all visualizations
        html.Div([
            dcc.Graph(id='nyc_map',  # add a graph component for nyc map to dashboard

                      # style map with an outline and set it to take up the left half of the screen
                      style={'width': '54%', 'height': '78vh', 'margin-left': '0px',
                             'display': 'inline-block', 'margin-top': '12px',
                             'border': '1.5px solid rgba(113, 156, 170, 0.5)'}
                      ),
            dcc.Graph(id='sankey_diagram',  # add a graph component for sankey to dashboard

                      # style sankey with an outline and set it to take up the top right half of the screen
                      style={'width': '54%', 'height': '40vh', 'margin-right': '0px',
                             'display': 'inline-block', 'vertical-align': 'top',
                             'margin-top': '12px', 'border': '1.5px solid rgba(113, 156, 170, 0.5)'}
                      ),
            dcc.Graph(id='histogram',  # add a graph component for histogram to dashboard

                      # style histogram with an outline and set it to take up the bottom right half of the screen
                      style={'width': '49.35%', 'height': '38vh', 'margin-right': '0px',
                             'display': 'inline-block', 'vertical-align': 'bottom',
                             'position': 'absolute', 'right': '8px', 'bottom': '0',
                             'margin-bottom': '9px', 'border': '1.5px solid rgba(113, 156, 170, 0.5)'}
                      )
        ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%'})
    ])

    # define the callback function for nyc_map with inputs determined by borough dropdown and year slider
    @app.callback(
        Output('nyc_map', 'figure'),
        [Input('borough_dropdown', 'value'),
         Input('year_range_slider', 'value')]
    )
    def update_nyc_map(selected_boroughs, selected_years):
        """
        :param selected_boroughs: boroughs chosen through dashboard dropdown
        :param selected_years: years chosen through dashboard slider
        :return: updates the nyc_map based on dashboard inputs
        """
        if not isinstance(selected_boroughs, list):
            selected_boroughs = [selected_boroughs]  # make sure that given boroughs are in list

        # return the generate nyc map function with new inputs
        return nd.generate_nyc_map(df, 'latitude', 'longitude', yr_start=selected_years[0],
                                   yr_end=selected_years[1], boroughs=selected_boroughs)

    # define the callback function for sankey_diagram
    # with inputs determined by borough dropdown, year slider, and sankey columns checklist
    @app.callback(
        Output('sankey_diagram', 'figure'),
        [Input('borough_dropdown', 'value'),
         Input('year_range_slider', 'value'),
         Input('sankey_columns_checklist', 'value')]
    )
    # define a function to actively update the histogram based on selected boroughs and years
    def update_sankey_diagram(selected_boroughs, selected_years, selected_columns):
        """
        :param selected_boroughs: boroughs chosen through dashboard dropdown
        :param selected_years: years chosen through dashboard slider
        :param selected_columns: columns selected for Sankey diagram
        :return: updates the sankey_diagram based on dashboard inputs
        """
        if not isinstance(selected_boroughs, list):
            selected_boroughs = [selected_boroughs]  # make sure that given boroughs are in list

        # account for if less than two variables are selected and display text asking to select more
        if len(selected_columns) < 2:
            return {
                'data': [],
                'layout': {
                    'annotations': [{
                        'text': 'Sankey: Please select two or more variables',
                        'showarrow': False,
                        'font': {'size': 18}
                    }],
                    'xaxis': {'visible': False},
                    'yaxis': {'visible': False}
                }
            }
        else:

            # return the generate sankey function with new inputs
            return nd.generate_sankey(df, cols=selected_columns,
                                      yr_start=selected_years[0], yr_end=selected_years[1],
                                      boroughs=selected_boroughs)

    # define the callback function for histogram with inputs determined by borough dropdown and year slider
    @app.callback(
        Output('histogram', 'figure'),
        [Input('borough_dropdown', 'value'),
         Input('year_range_slider', 'value')]
    )
    # define a function to actively update the histogram based on selected boroughs and years
    def update_histogram(selected_boroughs, selected_years):
        """
        :param selected_boroughs:
        :param selected_years:
        :return:
        """
        if not isinstance(selected_boroughs, list):
            selected_boroughs = [selected_boroughs]  # make sure that given boroughs are in list

        # return the generate histogram function with new inputs
        return nd.generate_hist(df, cols=['number_of_persons_injured', 'number_of_persons_killed'],
                                yr_start=selected_years[0], yr_end=selected_years[1],
                                boroughs=selected_boroughs)

    app.run_server(debug=True)


if __name__ == "__main__":
    main()
