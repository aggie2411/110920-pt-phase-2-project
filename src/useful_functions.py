#!/usr/bin/env python
# coding: utf-8

# In[6]:

import glob
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import folium
import geopandas
import geopy
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.diagnostic import linear_rainbow, het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, make_scorer
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import folium.plugins as plugins
import math
from math import sin, cos, sqrt, atan2, radians
from haversine import haversine
from itertools import combinations


def concat_col(df, newcol, col1, col2):
    '''provide dataframe, new column name, and two existing columns to be concatenated'''
    df[newcol] = df[col1].str.strip() + df[col2].str.strip()
    


def lookup(df, lu_type):
    """
    Return a dataframe from 'df' with 'LUType' == lu_type
    and 'LUItem' == lu_item (if specified)
    """
    return df[df.LUType == lu_type]


# In[4]:

def show_box(df, col):
    ''' 
    returns boxplot of df[col] vs df['SalePrice]
    
    Parameters:
    df: dataframe from which you want the col and SalePrice to be taken
    col: column of interest that you want to plot 
    
    '''
    sns.boxplot(x=col, y="SalePrice", data=df)


def replace_val(df, col, val1, val2):
    ''' 
    replaces all val1 entries in df[col] with val2
    
    Parameters:
    df: dataframe of interest
    col: column in which values will be changed
    val1: value to be replaced
    val2: new value
    
    '''
    df.loc[df[col]==val1, col] = val2
# In[ ]:



def get_dict(number, df):
    """
    Returns a dictionary for a specific lookup number in lookup_df
    
    Parameters:
    df: will only work for lookup_df - need to refine this function
    number: number in lookup_df 'LUItem' column that you want to map to a dictionary
    
    """
    df = lookup(df, number)
    dictionary = dict(zip(df['LUItem'].values, df['LUDescription'].str.strip().values))
    return dictionary

def get_qq(model, name):
    ''' returns qq plot model is the name of the model
    name is the plot title
    
    Parameters:
    model: sm.OLS().fit() - model which you want to see
    name: name that will appear in qq plot title
    
    '''
    residuals = model.resid
    fig = sm.graphics.qqplot(residuals, line='45', fit=True)
    fig.suptitle('{} QQ Plot'.format(name), fontsize=12)
    fig.show()
    
def get_resid(df, model):
    ''' 
    returns actual minus predicted plot (y axis) vs predicted values (x axis)
    for a given model. (residual plot) 
    
    Parameters:
    model: sm.OLS().fit() - model which you want to see
    df: dataframe from which you want Sale Price to be taken from    
        
    '''
    
    y = df['SalePrice']
    y_hat = model.predict()
    plt.figure(figsize=(8,5))
    plt.axhline(y = 0, color = 'r', linestyle = '-')
    plt.ylabel("Residuals (Actual - Predicted Sale Price)")
    plt.xlabel("Predicted Sale Price")
    plt.scatter(x=y_hat, y=y-y_hat, color="blue", alpha=0.2);
    plt.title('Residual Plot')
    plt.show()
    
    
def drop_outliers(data, col, n_std):
    """
    Return a dataframe without outliers
    
    Parameters:
    data: dataframe
    col: column to check for outliers
    n_std: number of standard deviations to consider when dropping outliers
    """
    return data[np.abs(data[col]-data[col].mean())<=(n_std*data[col].std())]

def calc_distances(lat_long, area, df):
    """
    Calculate the haversine distances from the locations in lat_long and city
    Parameters:
    lat_long: pd.series of lat/long tuples
    city: the lat/long tuple of a city
    """
    dists = []
    for loc in lat_long:
        dists.append(haversine((area),(loc),unit='km'))
    return pd.Series(dists, index=df.index)

def get_multicol(df):
    '''
    Returns correlation dataframe showing all variable pairs and their respective correlation coefficient between 0.7 and 1
    
    Parameters:
    df: dataframe you want correlation pairs for 
        
    '''
    new_df=df.corr().abs().stack().reset_index().sort_values(0, ascending=False)

    # zip the variable name columns (Which were only named level_0 and level_1 by default) in a new column named "pairs"
    new_df['pairs'] = list(zip(new_df.level_0, new_df.level_1))

    # set index to pairs
    new_df.set_index(['pairs'], inplace = True)

    #d rop level columns
    new_df.drop(columns=['level_1', 'level_0'], inplace = True)

    # rename correlation column as cc rather than 0
    new_df.columns = ['cc']

    # drop duplicates. This could be dangerous if you have variables perfectly correlated with variables other than themselves.
    # for the sake of exercise, kept it in.
    new_df.drop_duplicates(inplace=True)

    return new_df[(new_df.cc>.70) & (new_df.cc <1)]

def get_logresid(df, model, col):
    '''
    
    returns actual minus predicted plot (y axis) vs predicted values (x axis)
    for a given model. (residual plot) 
    
    Parameters:
    model: sm.OLS().fit() - model which you want to see
    df: dataframe from which you want Sale Price or other col to be taken from
    col: column that represents actual values i.e SalePrice_log
    
    
    '''
    y = df[col]
    y_hat = model.predict()
    plt.figure(figsize=(8,5))
    plt.axhline(y = 0, color = 'r', linestyle = '-')
    plt.ylabel("Residuals (Actual - Predicted Sale Price)")
    plt.xlabel("Predicted Sale Price")
    plt.scatter(x=y_hat, y=y-y_hat, color="blue", alpha=0.2);
    plt.title('Residual Plot')
    plt.show()
    
def get_map(df):
    '''
    returns map of all rows of a dataframe that contain 'latitude' and 'longitude' columns
    price and address of all properties are available by clicking on the marker
    
    Parameters:
    df: df which contains 'latitude' and 'longitude' columns
    
    '''
    #Create base map zoomed in to seattle
    map4=folium.Map(location=[47.5837012,-122.3984634],  tiles=None, zoom_start=7)
    folium.TileLayer('cartodbpositron', name='King County House Prices').add_to(map4)

    #Make Marker Cluster Group layer
    mcg = folium.plugins.MarkerCluster(control=False)
    map4.add_child(mcg)

    #Create layer of markers
    #Set marker popups to display name and address of service
    for row in df.iterrows():
        row_values=row[1]
        location=[row_values['latitude'], row_values['longitude']]
        popup=popup=('$' + str(row_values['SalePrice'])+'<br>'+'<br>'+ row_values['Address']+
                     '<br>'+'<br>'+row_values['DistrictName'])
        marker=folium.Marker(location=location, popup=popup, min_width=2000)
        marker.add_to(mcg)

    #Add layer control
    folium.LayerControl().add_to(map4)

    return map4

def map_feature_by_zipcode(zipcode_data, col):
    """
    Generates a folium map of Seattle
    :param zipcode_data: zipcode dataset
    :param col: feature to display
    :return: m
    """

    # read updated geo data
    king_geo = "cleaned_geodata.json"

    # Initialize Folium Map with Seattle latitude and longitude
    m = folium.Map(location=[47.35, -121.9], zoom_start=9,
                   detect_retina=True, control_scale=False)

    # Create choropleth map
    m.choropleth(
        geo_data=king_geo,
        name='choropleth',
        data=zipcode_data,
        # col: feature of interest
        columns=['ZipCode', col],
        key_on='feature.properties.ZIPCODE',
        fill_color='OrRd',
        fill_opacity=0.9,
        line_opacity=0.2,
        legend_name='house ' + col
    )

    folium.LayerControl().add_to(m)

    # Save map based on feature of interest
    m.save(col + '.html')

    return m