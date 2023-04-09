
#######################################################################################################################
#######################################################################################################################
######################################## IMPORTS ######################################################################
#######################################################################################################################
#######################################################################################################################

import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import plotly.offline as pyo

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import dash
from dash import dcc, Output, Input
from dash import html

from flask import Flask
import dash_bootstrap_components as dbc

#pip install raceplotly
from raceplotly.plots import barplot

#from spyder.widgets import tabs


#######################################################################################################################
#######################################################################################################################
######################################## START APP ####################################################################
#######################################################################################################################
#######################################################################################################################
server=Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.LITERA])


#######################################################################################################################
#######################################################################################################################
######################################## DATA #########################################################################
#######################################################################################################################
#######################################################################################################################

basedir = 'https://raw.githubusercontent.com/martasustelo/dsaa-dv-2023/master/datafiles/'

trades = pd.read_csv(basedir + "trades.csv", delimiter=',')
consump_price = pd.read_csv(basedir + "scatter_consumption_price.csv", delimiter=',')
consumption = pd.read_csv(basedir + "consumption.csv", delimiter=',')



####Data Cleaning

dfData_import = None
dfData = None
dfDataRaceCountries = None
dfDataRaceProducts = None
dfListCountriesforDataRace = None
dfListProductsforDataRace = None

lst_months_for_racecharts = ['01', '07']


## Functions to return data

def food_price_monitor_import():
    global dfData_import
    global dfListCountriesforDataRace
    global dfListProductsforDataRace
    #global dfData

    food_price_monitor_file = basedir + "food_price_monitor.csv"
    if dfData_import is None:

        # Import data
        dfData_import = pd.read_csv(food_price_monitor_file, sep=";", header="infer", decimal=".")

        # Filter data - I15-based values, exclude Turkey and Cyprus and EU
        dfFilters = {}
        dfFilters["unit"] = "I15"
        countries_exclusion_list = ["EA19", "EA20", "EU27_2020", "TR", "CY"] # Turkey, Cyprus
        dfData_import = dfData_import.loc[(dfData_import[list(dfFilters)] == pd.Series(dfFilters)).all(axis=1)]
        dfData_import = dfData_import[~dfData_import["countrycode"].isin(countries_exclusion_list)]

        # Add new features to dfData_import
        dfData_import["Year"] = [x[0:4] for x in dfData_import["date"]]

        # Merge data with country geoinfo
        df_country_points = pd.read_csv(basedir  + 'europe_points.csv')
        dfData_import = dfData_import.merge(df_country_points[["countrycode", "latitude", "longitude", "country"]], how='inner', left_on='countrycode', right_on='countrycode', copy=True)
        #dfData_import["pct"] = dfData_import["obs_value"].astype("float")-100
        ## inflation_from_start


        #Countries list
        dfx = sorted(dfData_import["country"].unique().tolist())
        dfx.insert(0, "All")
        dfListCountriesforDataRace = dfx

        #Products list
        dfx = sorted(dfData_import["prodname"].unique().tolist())
        dfx.insert(0, "All")
        dfListProductsforDataRace = dfx





def choroplethdata(minyear="2008", maxyear="2022", coicop="CP011"):
    #global dfData_import
    global dfData
    # Import data
    food_price_monitor_import()
    # Filter data - coicop, year
    dfFilters={}
    dfFilters["coicop"] = coicop
    dfData_temp=dfData_import.loc[(dfData_import[list(dfFilters)] == pd.Series(dfFilters)).all(axis=1)]

    # Filter data - year
    dfData_temp = dfData_temp[dfData_temp['date'].isin([str(minyear)+"-01", str(maxyear)+"-12"])]

    # Filter dfData_final to create dfmin and dfmax
    dfmin = dfData_temp[dfData_temp['date'] == str(minyear)+"-01"]
    dfmax = dfData_temp[dfData_temp['date'] == str(maxyear)+"-12"][['countrycode', 'obs_value']]

    # Merge dfmin and dfmax on the 'country' column
    merged_df = pd.merge(dfmin, dfmax, on='countrycode', suffixes=('', '_max'))

    # Calculate the inflation rate for each country using the obs_value columns of merged_df
    merged_df['inflation'] = (merged_df['obs_value_max'] - merged_df['obs_value']) / merged_df['obs_value']*100.0

    dfData = merged_df


def chartrace_countries(prodname="Food"):
    #global dfData_import
    global dfDataRaceCountries

    # Import data
    food_price_monitor_import()

    # Filter data - coicop, year
    dfFilters={}
    if prodname == "All":
        dfFilters["prodname"] = "Food"
    else:
        dfFilters["prodname"] = prodname

    dfDataRaceCountries = dfData_import.loc[(dfData_import[list(dfFilters)] == pd.Series(dfFilters)).all(axis=1)]

    dfDataRaceCountries = dfDataRaceCountries[dfDataRaceCountries['date'].str[-2:].isin(lst_months_for_racecharts)]



def chartrace_products(countries=None):
    #global dfData_import
    global dfDataRaceProducts
    #global dfDataRaceCountries
    #global dfDataRaceProducts

    # Import data
    food_price_monitor_import()

    dfDataRaceProducts = dfData_import.copy()

    # Filter data
    if countries is not None:
        if not countries == "All":
            dfFilters={}
            dfFilters["country"] = countries
            dfDataRaceProducts = dfDataRaceProducts.loc[(dfDataRaceProducts[list(dfFilters)] == pd.Series(dfFilters)).all(axis=1)]

    # dfDataRaceProducts = dfDataRaceProducts[dfDataRaceProducts['date'].str[-2:].isin(['01', '07'])]
    dfDataRaceProducts = dfDataRaceProducts[dfDataRaceProducts['date'].str[-2:].isin(lst_months_for_racecharts)]

    products_inclusion_list = ["CP0111", "CP0112","CP0113","CP0114","CP0115","CP0116","CP0117","CP01181","CP0121","CP0213"]

    dfDataRaceProducts = dfDataRaceProducts[dfDataRaceProducts["coicop"].isin(products_inclusion_list)]

    dfDataRaceProducts = dfDataRaceProducts.groupby(['prodname', 'date'])['inflation_from_start'].mean().reset_index()
    dfDataRaceProducts["ccountry"] = countries





choroplethdata("2008", "2022", "CP011")
chartrace_countries("Food")
chartrace_products("All")



####### - FINISH


#######################################################################################################################
#######################################################################################################################
######################################## APP ##########################################################################
#######################################################################################################################
#######################################################################################################################


years = sorted(consumption['year'].unique())
year_options = [{'label': str(year), 'value': year} for year in years]

years_consump_price = sorted(consump_price['year'].unique())
year_options_consump_price = [{'label': str(year), 'value': year} for year in years]



# App layout
app.layout = html.Div([

    ############################################## LOGO ################################################################
    html.Div(
        children=[
                html.Img(
                    src='https://th.bing.com/th/id/R.da23f6213f9fcfe4646a345d289427df?rik=V8Cfayni8kvR0Q&riu=http%3a%2f%2fwww.best-masters.com%2fassets%2fimg%2flogo_ecole%2fims-cmyk-logo1458573899.png&ehk=yBu4yGKXjl2h%2f6XrRZl6WsMGSlDcFvIVK4on4qekkfg%3d&risl=&pid=ImgRaw&r=0',
                    style={
                        'height': '50px',
                        'float': 'left',
                        'marginTop': '10px',
                        'marginLeft': '10px'
                        }
                ),
    ############################################## BANNER ###############################################################
            html.H1(children='',
            style={
            'textAlign': 'center', 'fontSize': '40px',
            'background-image': 'url("https://th.bing.com/th/id/R.ec9aff397c8efb1b8f3c14dcfefac194?rik=PEX%2fZnikxgkYOg&pid=ImgRaw&r=0")',
            'background-size': 'cover',
            'background-position':'center',
            #'backgroundColor': '#3E688C',
            'paddingTop': '150px',
            'paddingBottom': '150px',
            'color': '#FAFAFA',
            'opacity': 1
                }
            )
        ]
    ),
    ############################################## SUMMARY #############################################################
    dbc.Row([
        dbc.Col(
            html.Div(
                children=[
                    html.Br(),
                    html.H1(children='European Food Habits and Trends', style={'fontSize':'50px','width': '3000px', 'marginLeft': '70px'}),
                    html.Br(),
                    html.Label(
                        [
                            html.P(
                            'Europe has a diverse and nutritious culinary heritage, with food habits varying based on factors such as climate, geography, culture, and history.', style={'font-family': 'sans-serif'}),
                            html.P(['The dashboard provides ', html.Span('valuable insights into Europeans food habits by analyzing food prices, purchasing power, and trade patterns', style={'color': '#629B40', 'font-weight': 'bold'}),    '.'], style={'font-family': 'sans-serif'}),
                            html.P(['This information can help users better ',
                                    html.Span('understand each country culture and efforts toward healthy and sustainable consumption habits', style={'color': '#629B40', 'font-weight': 'bold'}),
                                   ', as well as address dietary issues and other decision-making processes.'], style={'font-family': 'sans-serif'})
                        ],
                        style={
                            'textAlign': 'justify',
                            'fontSize': '20px',
                            'background-size': 'cover',
                            'background-position': 'center',
                            'backgroundColor': '#FAFAFA',
                            'paddingTop': '0px',
                            'paddingBottom': '0px',
                            'borderRadius': '5px',
                            'width': '100%',
                            'height': '100%',
                            'marginLeft': '70px'
                        }
                    )
                ]
            ),
            width={"size": 6, "order": 1}
        )
        ,
        dbc.Row([
            dbc.Col(
                html.Div(
                    html.Img(
                        src='https://imgcloud.s3.us-east-1.wasabisys.com/APT8ffOBiR.png',
                        style={
                            'position': 'absolute',
                            'top': '78%',
                            'left': '80%',
                            'transform': 'translate(-50%, -50%)',
                            'zIndex': 0,
                            'height':'350px', 'weight':'350px'
                        }
                    )
                ), width={"size": 6, "order": 2})])

        ]),


    html.Br(),html.Br(), html.Br(), html.Br(),

    ####################################################################################################################
    ############################################## QUESTION 1 ##########################################################

    ############################################## BANNER ##########################################################
    html.Div(
            children=[html.Label('',
                                style={'color':'#FAFAFA',
                                        'textAlign': 'center', 'fontSize':'35px',
                                        'background-size': 'cover',
                                        'background-position':'center',
                                        'background-image': 'url("https://imgcloud.s3.us-east-1.wasabisys.com/IH6VdEhCju.jpg")',
                                        'paddingTop': '150px',
                                        'paddingBottom': '150px',
                                        'width': '100%',
                                        'height': '50px',
                                        'opacity': 1
                                       }
                                 ),
            ]
    ),

    html.Br(),

    ############################################## ROW ############################################################

    dbc.Row([

        ########################################### coluna 1 #################################
        dbc.Col(
        html.Div(
            children=[
                html.Br(),
                html.Br(),

                html.Label('Learn and explore about other cultures!',
                                style={'color':'white',
                                        'fontSize':'20px',
                                        'background-size': 'cover',
                                        'backgroundColor': '#629B40',
                                        'paddingTop': '20px',
                                        'paddingBottom': '50px',
                                        'borderRadius': '5px',
                                        'width': '100%',
                                        'height': '30px',
                                        'marginTop': '10px',
                                        'marginLeft': '20px',
                                        'text-align': 'center'
                                       }
                                 ),
                html.Br(),
                html.Label('Select a Country', style={'font-weight': 'bold', 'color': 'black',
                                                    'marginTop': '10px',
                                                    'marginLeft': '40px'}),
                    dcc.Dropdown(
                                id='country-dropdown',
                                options=[{'label': i, 'value': i} for i in consumption['country'].unique()],
                                multi=False,
                                value=consumption['country'].unique()[-1],
                                placeholder="Select a country",
                                clearable=False,
                                style={ 'backgroundColor': '#FAFAFA',
                                        'color': 'black',
                                        'borderWidth': '1px',
                                        'marginTop': '10px',
                                        'marginLeft': '20px'}
                    ),
                      html.Label('Select a Year', style={'font-weight': 'bold', 'color': 'black',
                                                       'marginTop': '10px',
                                                       'marginLeft': '40px'}),
                      html.Br(),
                      dcc.Dropdown(
                        id='year-dropdown',
                        options=year_options,
                        value = min(years),
                        clearable=False,
                        style={ 'backgroundColor': '#FAFAFA',
                                'color': 'black',
                                'borderWidth': '1px',
                                'marginTop': '10px',
                                'marginLeft': '20px'
                                }
                    )


            ]
        ),
        width={"size": 4, "order": 1}
    ),

        ########################################### coluna 2 #################################

        dbc.Col(
            html.Div(
                children=[
                    dcc.Graph(id='fig_consumption',
                        config={
                            'displayModeBar': False,
                        },
                        style={
                            'width': 'calc(100%)',  # subtraindo 100px da largura
                            'height': 'calc(500px)',  # subtraindo 100px da altura
                            'border-radius': '50%',
                            'position': 'relative',
                            'zIndex': 2}
                    ),
                    html.Img(
                        src='https://imgcloud.s3.us-east-1.wasabisys.com/Jn5QIkoqFI.png',
                        style={
                            'position': 'absolute',
                            'top': '187%',
                            'left': '68.2%',
                            'transform': 'translate(-50%, -50%)',
                            'zIndex': 1,
                            'weight': '100%',
                            'height': '450px'
                        }
                    )
                ],
                style={
                    'padding': '10px',
                    'borderRadius': '5px',
                    'width': '100%',
                    'height': '100%',
                }
            ),

        width={"size": 8, "order": 2}
    )


    ]
    ),


    html.Br(),

    ####################################################################################################################
    ############################################## QUESTION 2 ##########################################################

    ############################################## BANNER ##############################################################
    html.Div(
        children=[html.Label('',
                             style={'color': '#FAFAFA',
                                    'textAlign': 'center', 'fontSize': '40px',
                                    'background-size': 'cover',
                                    'background-position': 'center',
                                    'background-image': 'url("https://imgcloud.s3.us-east-1.wasabisys.com/mePva8lDFv.jpg")',
                                    'paddingTop': '150px',
                                    'paddingBottom': '150px',
                                    'width': '100%',
                                    'height': '50px',
                                    'opacity': 0.7
                                    }
                             ),
                  ]
    ),

    ############################################## ROW 1 ###############################################################
    dbc.Row([

    ############################################## COLUMN 1 ############################################################
        dbc.Col(
            html.Div(
                children=[

                    html.Br(),
                    dcc.Graph(id='fig_choropleth', figure={}, style={'height': '600px'}),
                    html.Br(),
                    #region range slider
                    dcc.RangeSlider(
                        id='year_slider_choropleth',
                        min=2008,
                        max=2022,
                        value=[2008, 2022],
                        marks={'2008': '2008',
                               '2009': '2009',
                               '2010': '2010',
                               '2011': '2011',
                               '2012': '2012',
                               '2013': '2013',
                               '2014': '2014',
                               '2015': '2015',
                               '2016': '2016',
                               '2017': '2017',
                               '2018': '2018',
                               '2019': '2019',
                               '2020': '2020',
                               '2021': '2021',
                               '2022': '2022'
                               }, className='custom-range-slider',
                        step=3
                    ), # endregion range slider

                ],
                ), width={"size": 6}),

    ############################################## COLUMN 2 ############################################################
        dbc.Col(
            html.Div(
                children=[
                    html.Br(),

                    ############################################## TAB 1 ###############################################
                    dbc.Tabs(



                        id="tabs",
                        active_tab="tab_country",
                        style={
                            "color": "black",
                            "background-color": "#f8f9fa",
                            "border": "none",
                            "font-weight": "bold"},
                        children=[
    
                             dbc.Tab(
                                label="Country",
                                tab_id="tab_country",
                                active_tab_style={"color": "black"},
                                style={
                                    "color": "black",
                                    "background-color": "#f8f9fa",
                                    "border": "none",
                                    "font-weight": "bold"},
                                children=[
    
                               html.Label('Select a Product', style={'font-weight': 'bold', 'color': 'black',
                                                                    'marginTop': '10px',
                                                                    'marginLeft': '0px',
                                                                    'marginRight': '40px'}),
                                    dcc.Dropdown(
                                                id='race_product_dropdown',
                                                
                                                options = dfListProductsforDataRace,
                                                multi=False,
                                                value="All",
                                                placeholder="All",
                                                style={ 'backgroundColor': '#FAFAFA',
                                                        'color': 'black',
                                                        #'borderColor': 'black','borderWidth': '1px','marginTop': '10px','marginLeft': '20px'
                                                        },
                                                clearable=False),
                                    html.Br(),


                                    dcc.Graph(
                                        id='fig_countryraceplot',
                                        figure={},
                                        style={"xaxis": {"color": "black"}, "yaxis": {"color": "black"}},
                                    )
                                ]
                            ),
                    ############################################## TAB 2 ###############################################
                            dbc.Tab(
    
                                 label='Products',
                                tab_id='tab_products',
                                children=[
                                html.Label('Select a Country', style={'font-weight': 'bold', 'color': 'black',
                                                                    'marginTop': '10px',
                                                                    'marginLeft': '0px',
                                                                    'marginRight': '40px'}),
                                    dcc.Dropdown(
                                                id='race_country_dropdown',
                                                
                                                options = dfListCountriesforDataRace,
                                                multi=False,
                                                value="All",
                                                placeholder="All",
                                                style={ 'backgroundColor': '#FAFAFA',
                                                        'color': 'black',
                                                        #'borderColor': 'black','borderWidth': '1px','marginTop': '10px','marginLeft': '20px'
                                                        },
                                                clearable=False),
                                    html.Br(),
                                    dcc.Graph(id='fig_productraceplot', figure={})
                                ]
                            )
                        ]


                    ) #endregion tab_products


                ] # end tabs.children
            ) # end div
        ), # end col
    ]), # end row

    ####################################################################################################################
    ############################################## QUESTION 3 ##########################################################

    ############################################## BANNER ##############################################################

    html.Div(
        children=[html.Label('',
                             style={'color': '#FAFAFA',
                                    'textAlign': 'center', 'fontSize': '40px',
                                    'background-size': 'cover',
                                    'background-position': 'center',
                                    'background-image': 'url("https://imgcloud.s3.us-east-1.wasabisys.com/eKGoGXei63.jpg")',
                                    'paddingTop': '150px',
                                    'paddingBottom': '150px',
                                    'width': '100%',
                                    'height': '50px',
                                    'opacity': 0.7
                                    }
                             ),
                  ]
    ),

    html.Br(),

    ############################################## ROW 1 ###############################################################
    dbc.Row([
        ############################################## COLUMN 1 ########################################################
        dbc.Col(
            html.Div(
                children=[

                    dcc.Graph(id='fig_consump_price', figure={}),

                ]
            ),
            width={"size": 7, "order": 1}
        ),

        ############################################## COLUMN 2 ########################################################
        dbc.Col(
            html.Div(
                children=[
                    html.Br(),
                    html.Label('Select a Country', style={'font-weight': 'bold', 'color': 'black',
                                                        'marginTop': '10px',
                                                        'marginLeft': '-100px'}),
                    dcc.Dropdown(
                        id='country_consump_price',
                        options=[{'label': i, 'value': i} for i in consump_price['country'].unique()],
                        multi=False,
                        clearable=False,
                        value=consump_price['country'].unique()[-1],
                        placeholder="Select a country",
                        style={'backgroundColor': '#FAFAFA',
                               'color': 'black',
                               # 'borderColor': 'black',
                               'borderWidth': '1px',
                               'marginTop': '10px',
                               'marginLeft': '-49px',
                               'width':'500px'}),

                    html.Label('VS. Europe', style={'font-weight': 'bold', 'color': 'black', 'width':'500px',
                                                        'marginTop': '10px',
                                                        'marginLeft': '-40px', 'fontSize': '25px'}),
                    html.Br(),
                    html.Br(),

                    dbc.Col(
                        dbc.Card(id='card_hicp'),  # create empty Card component
                    ),
                ],
                style={
                    'padding': '10px',
                    'borderRadius': '5px',
                    'width': '100%',
                    'height': '100%',
                    'marginLeft': '100px'
                }
            ),
            width={"size": 2, "order": 2}
        ),

        dbc.Col(
            html.Div(
                children=[
                    html.Br(), html.Br(), html.Br(), html.Br(), html.Br(),
                    html.Br(), html.Br(),



                    dbc.Col(
                        dbc.Card(id='card_consump'),  # create empty Card component
                    ),
                ],
                style={
                    'padding': '10px',
                    'borderRadius': '5px',
                    'width': '100%',
                    'height': '100%',
                    'marginLeft': '100px'
                }
            ),
            width={"size": 2, "order": 3}
        )

    ]
    ),


    html.Br(), html.Br(),

    ####################################################################################################################
    ############################################## QUESTION 4 ##########################################################

    html.Div(
            children=[html.Label(' ',
                                 style={'color': '#FAFAFA',
                                        'textAlign': 'center', 'fontSize': '40px',
                                        'background-size': 'cover',
                                        'background-position': 'center',
                                        'background-image': 'url("https://imgcloud.s3.us-east-1.wasabisys.com/8TQxNtPzEm.jpg")',
                                        'paddingTop': '150px',
                                        'paddingBottom': '150px',
                                        'width': '100%',
                                        'height': '50px',
                                        'opacity': 0.75
                                        }
                                 ),
                      ]
        ),
    dbc.Row([
         ########################################### coluna 2 #################################

        dbc.Col(
            html.Div(
                children=[
                    html.Br(),
                    html.Label('Select a Country', style={'font-weight': 'bold'}),
                    html.Br(),
                    dcc.Dropdown(
                                id='country_drop',
                                options=[{'label': i, 'value': i} for i in trades['country'].unique()],
                                multi=False,
                                clearable=False,
                                value=trades['country'].unique()[0],
                                placeholder="Select a country",
                                style={ 'backgroundColor': 'white',
                                        'color': 'black',
                                        'borderWidth': '1px'}
                    ),
                    html.Br(),
                    dcc.Graph(id='fig_trades'),
                ],
                style={
                    'padding': '10px',
                    'borderRadius': '5px',
                    'width': '100%',
                    'height': '100%',
                }
            ),

        width={"size":6, "order": 2}
    ),

        dbc.Col(
            html.Div(
                children=[
                    html.Br(),
                    html.Label('Select a Year', style={'font-weight': 'bold'}),
                html.Br(),
                dcc.Dropdown(
                        id='year_drop',
                        options=[{'label': i, 'value': i} for i in trades['year'].unique()],
                        multi=False,
                        clearable=False,
                        value=trades['year'].unique()[0],
                        placeholder="Select a year",
                        style={'backgroundColor': 'white',
                              'borderWidth': '1px'}
                    ),
                    html.Br(),
                    dcc.Graph(id='fig_trades_compare'),

                ],
                style={
                    'padding': '10px',
                    'borderRadius': '5px',
                    'width': '100%',
                    'height': '100%',}
            ), width={"size": 6, "order": 3})


    ],
    ),
    html.Br(), html.Br(),

    html.Div(
        children=[
            html.Label([html.Span("European Food Habits & Trends", style={'font-weight': 'bold'}),
                       html.P("by António Samuel Santos | Ana Marta Santos | João Ferreira | Margarida Pereira",style={'font-family': 'sans-serif', 'fontSize': '20px'} )], style={'color': '#FAFAFA',
                                    'font-family': 'sans-serif',
                                    'textAlign': 'center', 'fontSize': '22px',
                                    'background-size': 'cover',
                                    'background-position': 'center',
                                    'backgroundColor': '#629B40',
                                    'paddingTop': '50px',
                                    'paddingBottom': '100px',
                                    'width': '100%',
                                    'height': '20px',
                                    'opacity': 1
                                    })
        ]

    )
], style={'backgroundColor': '#FAFAFA'})



# Connect the Plotly graphs with Dash Components
@app.callback(
    Output('fig_consumption', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('country-dropdown', 'value')]
)
def update_graph_consumption(year, country):
    df_year = consumption.loc[(consumption['year'] == year) & (consumption['country'] == country), :]

    # Create a sequence of layers based on the Subcategory column
    layers = df_year.groupby(['category', 'group', 'subgroup']).apply(
        lambda x: x['subgroup'].iloc[-1]).reset_index()

    fig_consumption = px.sunburst(df_year, path=['category', 'group', 'subgroup'], values='consumption',
                                  color_discrete_sequence=['#629B40', px.colors.qualitative.Pastel[1]])

    fig_consumption.update_layout(
        title={
        'text': '<b>Dietary Habits: Daily Caloric Consumption by Food Group',
        'font': {'size': 25, 'color': 'black'}},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig_consumption


@app.callback(
    Output(component_id='fig_trades', component_property='figure'),
    Input(component_id='country_drop', component_property='value')
)

def update_graph_trades(option_slctd):
    df = trades.copy()
    dff = df[(df['country'] == option_slctd)]

    fig_trades = go.Figure()

    # Add imports trace
    fig_trades.add_trace(
        go.Scatter(x=dff['year'], y=dff['imports'], name='Imports',
                   line=dict(color='#F6CF71', width=2))
    )

    # Add exports trace
    fig_trades.add_trace(
        go.Scatter(x=dff['year'], y=dff['exports'], name='Exports',
                   line=dict(color='#629B40', width=2))
    )

    # Add airplane icon at last year
    last_year = dff['year'].max()
    last_imports = dff.loc[dff['year'] == last_year, 'imports'].iloc[0]
    last_exports = dff.loc[dff['year'] == last_year, 'exports'].iloc[0]

    fig_trades.add_trace(
        go.Scatter(x=[last_year], y=[last_imports],
                   mode='text', name='Airplane',
                   text='🛬', textfont=dict(size=25), textposition='middle right',
                   showlegend=False)
    )
    fig_trades.add_trace(
        go.Scatter(x=[last_year], y=[last_exports],
                   mode='text', name='Airplane',
                   text='🛩️', textfont=dict(size=25), textposition='middle right', showlegend=False)
    )

    # Set layout
    fig_trades.update_layout(
        title={
            'text': '<b>Trades: Imports and Exports in {}'.format(option_slctd),
            'font': {'size': 25, 'color': 'black'},
        },
        yaxis_title='Amount (Millions€)',
        xaxis=dict(
            title='Years',
            titlefont=dict(color='black'),
            tickfont=dict(color='black')
        ),
        yaxis=dict(
            titlefont=dict(color='black'),
            tickfont=dict(color='black')
        ),
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.5,
            'xanchor': 'center',
            'x': 0.5,
            'title': {
                'text': '',
                'font': {'size': 12, 'color': 'black'}
            },
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',

    )

    return fig_trades


@app.callback(
    Output('fig_trades_compare', component_property='figure'),
    Input(component_id='year_drop', component_property='value')
)
def update_graph(option_slctd):
    df = trades.copy()
    dff = df[(df['year'] == option_slctd)]

    top_countries = dff.groupby('country')[['exports', 'imports']].sum().sum(axis=1).sort_values(
        ascending=False)[:10].index.tolist()
    dfff = trades.loc[df['country'].isin(top_countries)].groupby('country')[
        [ 'exports', 'imports']].sum().reset_index()

    # Create the figure object using Plotly Express
    fig_trades_compare = go.Figure()

    # Add the imports trace to the figure, with x-values on the left
    fig_trades_compare.add_trace(go.Bar(
        y=dfff['country'],
        x=-dfff['imports'],  # Set the x-axis values as negative for the imports
        name='Imports',
        orientation='h',
        marker_color='#F6CF71'
    ))

    # Add the exports trace to the figure, with x-values on the right
    fig_trades_compare.add_trace(go.Bar(
        y=dfff['country'],
        x=dfff['exports'],
        name='Exports',
        orientation='h',
        marker_color='#629B40'
    ))

    # Update the layout of the figure
    fig_trades_compare.update_layout(
        barmode='overlay',  # Set the barmode to 'overlay'
        title={
            'text': '<b>Top 10 Countries by Trade',
            'font': {'size': 25, 'color':'black'},
        },
        xaxis=dict(
            title='Trade in Millions €',
            titlefont=dict(color='black'),
            tickfont=dict(color='black'),
            zeroline=False,  # Hide the zero line to prevent overlapping of bars
        ),
        yaxis=dict(
            tickfont=dict(color='black')
        ),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')

    return fig_trades_compare



@app.callback(
    Output('fig_consump_price', 'figure'),
    [
    Input('country_consump_price', 'value')]
)

def update_graph_consumption_price(country):
    dff = consump_price[(consump_price['country'] == country)]

    fig_consump_price = px.scatter(dff,
                                   x="consumption",
                                   y="hicp",
                                   color='foodcategories',
                                   symbol='foodcategories',
                                   animation_frame='year',
                                   symbol_sequence=['circle', 'square', 'diamond', 'cross', 'pentagon'],
                                   color_discrete_sequence=['#C6F092', '#7E9C34', '#866F3F', '#00786C', '#CD9F21'])

    axis_text_color = 'black'

    fig_consump_price.update_xaxes(title=dict(text='consumption', font=dict(color=axis_text_color)),
                                   tickfont=dict(color=axis_text_color))

    fig_consump_price.update_yaxes(title=dict(text='hicp', font=dict(color=axis_text_color)),
                                   tickfont=dict(color=axis_text_color))

    fig_consump_price.update_layout(legend=dict(font=dict(color='black')))

    fig_consump_price.update_xaxes(range=[min(dff['consumption'] - 10), max(dff['consumption']) + 10])
    fig_consump_price.update_yaxes(range=[min(dff['hicp']) - 10, max(dff['hicp']) + 10])

    # Atualizar os valores da linha do tempo (slider) para preto
    for step in fig_consump_price.layout.sliders[0].steps:
        step["args"][1]["frame"]["redraw"] = True
        step["args"][1]["sliderlabel"] = {"text": step['label'], "font": {"color": "black"}}

    fig_consump_price.update_layout(
        title={
            'text': '<b>Relationship between Consumption and HICP',
            'font': {'size': 25, 'color': 'black'}},
        yaxis_title = 'HICP',
        xaxis = dict(
            title='Consumption',
            titlefont=dict(color='black'),
            tickfont=dict(color='black')
        ),
        yaxis=dict(
            titlefont=dict(color='black'),
            tickfont=dict(color='black')
        ),
        legend={
            'title':'Food Category'
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)')

    fig_consump_price.update_traces(marker=dict(size=13))
    return fig_consump_price

#region Choropleth

@app.callback(
    Output(component_id='fig_choropleth', component_property='figure'),
    Input(component_id='year_slider_choropleth', component_property='value')
)
def update_choropleth(year):

    minyear = year[0]
    maxyear = year[1]

    mycolorscale = ['#233817', '#629B40', '#CBE4BD','#CDC121', '#CD9F21', '#CD7C21' ]

    choroplethdata(minyear=minyear, maxyear=maxyear, coicop='CP011')

    data_choropleth = dict(type='choropleth',
                        locations=dfData['country'],  #There are three ways to 'merge' your data with the data pre embedded in the map
                        locationmode='country names',
                        z=dfData['inflation'],
                        text=dfData['country'],
                        colorscale=mycolorscale
                        )

    layout_choropleth = dict(geo=dict(scope='europe',
                                    projection=dict(type='natural earth'),
                                    showland=True,
                                    landcolor='#FAFAFA',
                                    lakecolor='#FAFAFA',
                                    showocean=False,
                                    oceancolor='#FAFAFA',
                                    bgcolor = '#FAFAFA',
                                    showcountries=True,
                                    countrycolor='rgba(0,0,0,0)'),
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    margin=dict(l=0, r=0, b=50, t=50, pad=0),
                                    title=dict(text='<b>Price Increase (%), from {}/01 to {}/12'.format(minyear, maxyear),
                                               font=dict(
                                                   family='Arial',
                                                   size=25,
                                                   color='black',
                                                   #style='bold'
                                               )),
                                    coloraxis=dict(colorscale=[[0, 'white']])
                            )
    fig_choropleth = go.Figure(data=data_choropleth, layout=layout_choropleth)

    return fig_choropleth
#endregion




@app.callback(
    Output(component_id='fig_countryraceplot', component_property='figure'),
    Input( component_id = 'race_product_dropdown', component_property='value')
)
def update_racechartcountry(product):
    chartrace_countries(product)

    my_countryraceplot = barplot(dfDataRaceCountries,
                                 item_column ='country',
                                 value_column ='inflation_from_start',
                                 time_column = 'date')
    my_countryraceplot.plot(item_label='Countries',
                            value_label='Inflation (%)',
                            frame_duration=130
                            )
    my_countryraceplot.fig.layout.plot_bgcolor = '#FAFAFA'
    my_countryraceplot.fig.layout.paper_bgcolor = '#FAFAFA'
    my_countryraceplot.fig.update_layout(height=560)

    fig_countryraceplot = go.Figure(my_countryraceplot.fig)

    fig_countryraceplot.update_layout(
        title={
            'text': '<b>Top 10 countries most affected by inflation<b>',
            'font': {'color': 'black', 'size': 25}
        },
        xaxis_title='Inflation (%)',
        yaxis_title='Countries',
        xaxis=dict(
            titlefont=dict(color='black', size=12),
            tickfont=dict(color='black', size=10)
        ),
        yaxis=dict(
            titlefont=dict(color='black', size=12),
            tickfont=dict(color='black', size=10)
        ),
        plot_bgcolor='#FAFAFA',
        paper_bgcolor='#FAFAFA',
        height=560
    )

    return fig_countryraceplot


from plotly.subplots import make_subplots

@app.callback(
    Output(component_id='fig_productraceplot', component_property='figure'),
    Input(component_id='race_country_dropdown', component_property='value')
)
def update_racechartproduct(country):
    chartrace_products(country)

    # Criar um gráfico de barras animado usando Plotly Express
    fig_productraceplot = px.bar(dfDataRaceProducts,
                                 y="prodname",
                                 x="inflation_from_start",
                                 orientation='h',
                                 animation_frame="date",
                                 range_x=[0, dfDataRaceProducts["inflation_from_start"].max() * 1.1],
                                 title='<b>Top 10 products most affected by inflation</b>',
                                 labels={'prodname': 'Products','inflation_from_start': 'Inflation (%)'})

    fig_productraceplot.update_layout(
        title={
        'text': '<b>Top 10 products most affected by inflation<b>',
        'font': {'size': 20, 'color': 'black'}},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Atualizar layout e configurações do gráfico
    fig_productraceplot.update_layout(transition={'duration': 130},
                                      updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='Play',
                                                                                                        method='animate',
                                                                                                        args=[None, {
                                                                                                            'frame': {
                                                                                                                'duration': 130,
                                                                                                                'redraw': True},
                                                                                                            'fromcurrent': True}]),
                                                                                                   dict(label='Stop',
                                                                                                        method='animate',
                                                                                                        args=[[None], {
                                                                                                            'frame': {
                                                                                                                'duration': 0,
                                                                                                                'redraw': False},
                                                                                                            'mode': 'immediate',
                                                                                                            'fromcurrent': True}])])],
                                      xaxis_title="Inflation (%)",
                                      yaxis_title="Products",
                                      plot_bgcolor='#FAFAFA',
                                      paper_bgcolor='#FAFAFA',
                                      height=560)

    # Atualizar as cores das barras
    n_frames = len(fig_productraceplot.frames)
    for frame in fig_productraceplot.frames:
        frame_data = frame['data']
        colors = ['#233817', '#629B40', '#CBE4BD','#CDC121', '#CD9F21', '#CD7C21', '#FFC300', '#FFA500', '#FF8C00', '#FF7F50']  # Amarelo, Verde, Verde claro, Laranja, Bege, Laranja escuro
        frame_data[0]['marker'] = {'color': colors}

    colors = ['#233817', '#629B40', '#CBE4BD','#CDC121', '#CD9F21', '#CD7C21', '#FFC300', '#FFA500', '#FF8C00', '#FF7F50']  # Amarelo, Verde, Verde claro, Laranja, Bege, Laranja escuro
    fig_productraceplot.data[0].marker.color = colors



    return fig_productraceplot








@app.callback(
    Output('card_consump', 'children'), # update the children property of the card component
    [Input('country_consump_price', 'value')]
)
def update_card_consumption(country):
    # Calculate the average consumption across all countries
    avg_consumption_all = np.mean(consump_price['consumption'])

    # Calculate the average consumption across all countries
    dff = consump_price[(consump_price['country'] == country)]
    avg_consumption_country = np.mean(dff['consumption'])

    # Calculate variance
    variance= (avg_consumption_country - avg_consumption_all) * 100 /avg_consumption_all

    if avg_consumption_country > avg_consumption_all:
        # Show a success card if consumption is higher than the average
        card_consump = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Consumption Above Average", className="card-title"),
                    html.P([country, " has registered a higher average in consumption of ", round(variance,2), '% when compared to the EU values.'
                            ], className="card-text", style={'fontSize': '14px', 'font-family': 'sans-serif'}),
                ]
            ),
            style={"width": "230px", "height": "15rem","background-color": "#82AA6A", "color": "white",'fontSize': '13px', 'font-family': 'sans-serif'},
        )
    else:
        # Show a danger card if consumption is lower than the average
        card_consump = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Consumption Below Average", className="card-title"),
                    html.P([country, " has registered a lower average in consumption of ", round(variance,2), '% when compared to the EU values.'
                            ], className="card-text", style={'fontSize': '14px', 'font-family': 'sans-serif'}),
                ]
            ),
            style={"width": "230px", "height": "15rem", "background-color": "#F6CF71", "color": "white",'fontSize': '13px', 'font-family': 'sans-serif'},
        )

    return card_consump

@app.callback(
    Output('card_hicp', 'children'), # update the children property of the card component
    [Input('country_consump_price', 'value')]
)
def update_card_price(country):
    # Calculate the average consumption across all countries
    avg_hicp_all = np.mean(consump_price['hicp'])

    # Calculate the average consumption across all countries
    dff = consump_price[(consump_price['country'] == country)]
    avg_hicp_country = np.mean(dff['hicp'])

    # Calculate variance
    variance= (avg_hicp_country - avg_hicp_all) * 100 /avg_hicp_all

    if avg_hicp_country < avg_hicp_all:
        # Show a success card if hicp is below  the average
        card_hicp = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("€ Stability Above Average", className="card-title"),
                    html.P([country, " has registered a lower average in HICP of ", round(variance,2), '% when compared to the EU values.'
                            ], className="card-text", style={'fontSize': '14px', 'font-family': 'sans-serif'}),
                ]
            ),
            style={"width": "230px", "height": "15rem", "background-color": "#82AA6A", "color": "white",'fontSize': '13px', 'font-family': 'sans-serif'}
        )
    else:
        # Show a danger card if hicp is higher  the average
        card_hicp = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("€ Stability Below Average", className="card-title"),
                    html.P([country, " has registered a higher average in HICP of ", round(variance,2), '% when compared to the EU values.'
                            ], className="card-text", style={'fontSize': '14px', 'font-family': 'sans-serif'}),
                ]
            ),
            style={"width": "230px", "height": "15rem", "background-color": "#F6CF71", "color": "white", 'fontSize': '13px', 'font-family': 'sans-serif'}
        )

    return card_hicp



if __name__ == '__main__':
   app.run_server(debug=True)
