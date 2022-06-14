import os
import pandas as pd


def get_stocks_with_weekly_options():
    """ Returns set of all stocks with weekly options"""
    weeklyOptions = pd.read_csv(os.path.join('input_data','cboesymboldirweeklys.csv'))
    weeklyOptions.columns = ['name', 'symbol']
    weeklySet = set(weeklyOptions['symbol'])
    return weeklySet
    
def get_stocks_with_options():
    """ Returns set of all stocks with options"""
    indexOptions = pd.read_csv(os.path.join('input_data','cboesymboldirequityindex.csv'))
    indexOptions.drop(columns = [' DPM Name', ' Post/Station'], inplace=True)
    indexOptions.columns = ['name', 'symbol']
    optionSet = set(indexOptions['symbol'])
    return optionSet
