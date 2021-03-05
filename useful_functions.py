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
    df[newcol] = df[col1].str.strip() + df[col2].str.strip()
    


def lookup(df, lu_type):
    """
    Return a dataframe from 'df' with 'LUType' == lu_type
    and 'LUItem' == lu_item (if specified)
    """
    return df[df.LUType == lu_type]


# In[4]:

def show_box(df, col):
    sns.boxplot(x=col, y="SalePrice", data=df)


def replace_val(df, col, val1, val2):
    df.loc[df[col]==val1, col] = val2
# In[ ]:



def get_dict(number, df):
    df = lookup(df, number)
    dictionary = dict(zip(df['LUItem'].values, df['LUDescription'].str.strip().values))
    return dictionary

def get_qq(model, name):
    residuals = model.resid
    fig = sm.graphics.qqplot(residuals, line='45', fit=True)
    fig.suptitle('{} QQ Plot'.format(name), fontsize=12)
    fig.show()
    
def get_resid(df, model):
    y = df['SalePrice']
    y_hat = model.predict()
    plt.figure(figsize=(8,5))
    plt.axhline(y = 3, color = 'r', linestyle = '-')
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