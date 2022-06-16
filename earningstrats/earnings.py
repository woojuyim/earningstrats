import yfinance as yf
import pandas as pd
import yahoo_fin.stock_info as si
from datetime import datetime, timedelta, date
import os
from earningstrats.option_set import *
from earningstrats.util import *
from earningstrats.options import get_expected_move, get_put_option_chain, get_earliest_deadline_options_chain

pd.options.display.float_format = '{:.4f}'.format

def get_stock_earnings_price_effect(symbol, period = "5y"):
    """ Get Earnings Price Effect. Returns Pandas DataFrame with Data of Market Close to Next Day Open and Close
    Set period to set cutoff
    """
    stock = yf.Ticker(symbol)
    hist = stock.history(period)
    earn_hist = si.get_earnings_history(symbol)
    data = {}
    is_AMC = earn_hist[0]['startdatetimetype'] == "AMC" #Default AMC
    for earning in earn_hist: 
        earn_date = earning['startdatetime']
        dt_obj = datetime.strptime(earn_date, '%Y-%m-%dT%H:%M:%S.000Z')
        date = dt_obj.date()
        
        # If hour is < 14, count as BMO, else count as AMC
        if(dt_obj.hour < 14): 
            is_AMC = False
        else:
            is_AMC = True

        if is_AMC:
            earning_day = hist.loc[(hist.index == str(date))]
            earning_next_day = hist.loc[hist.index == str(date + timedelta(days = 1))]
            if not earning_day.empty and not earning_next_day.empty:
                earning_effect_close_to_next_open = earning_next_day["Open"].iloc[0] - earning_day["Close"].iloc[0]
                earning_effect_close_to_next_close = earning_next_day["Close"].iloc[0] -  earning_day["Close"].iloc[0]

                data[str(date)] = [earning_effect_close_to_next_open, 
                                  earning_effect_close_to_next_open * 100 / earning_day["Close"].iloc[0] ,
                                   earning_effect_close_to_next_close ,
                                  earning_effect_close_to_next_close * 100 / earning_day["Close"].iloc[0]]

        else:
            earning_day = hist.loc[(hist.index == str(date))]
            earning_prev_day = hist.loc[hist.index == str(date - timedelta(days = 1))]
            if not earning_day.empty and not earning_prev_day.empty:
                earning_effect_prev_close_to_open = earning_day["Open"].iloc[0] -  earning_prev_day["Close"].iloc[0]
                earning_effect_prev_close_to_close = earning_day["Close"].iloc[0] -  earning_prev_day["Close"].iloc[0]

                data[str(date)] = [earning_effect_prev_close_to_open,
                                  earning_effect_prev_close_to_open * 100/ earning_prev_day["Close"].iloc[0] ,
                                   earning_effect_prev_close_to_close,
                                  earning_effect_prev_close_to_close * 100/ earning_prev_day["Close"].iloc[0]]

    earn_data = pd.DataFrame.from_dict(data, orient='index',
                columns=['day_close_to_next_day_open', '%change_close_to_next_open',
                        'day_close_to_next_day_close', '%change_close_to_next_close'])
    
    new_row = pd.DataFrame({'day_close_to_next_day_open':earn_data['day_close_to_next_day_open'].abs().mean(), '%change_close_to_next_open':earn_data['%change_close_to_next_open'].abs().mean(), 
                            'day_close_to_next_day_close':earn_data['day_close_to_next_day_close'].abs().mean(), '%change_close_to_next_close':earn_data['%change_close_to_next_close'].abs().mean()}, 
                           index=["Absolute Average"])

    earn_data = pd.concat([earn_data, new_row])
    earn_data.insert(0, 'Symbol', symbol)

    return earn_data


def get_companies_with_earnings_today_AMC_or_tomm_BMO(day_shift = 0, min_vol_sum = 3000, min_stock_price = 10):
    curr_date = datetime.now().date() +  timedelta(day_shift)
        
    earn_today = si.get_earnings_for_date(str(curr_date))
    earn_tomm = si.get_earnings_for_date(str(curr_date + timedelta(1)))
    
    comp_today = pd.DataFrame.from_dict(earn_today)
    comp_tomm = pd.DataFrame.from_dict(earn_tomm)

    # print_full(comp_today)
    # print_full(comp_tomm)        
    if comp_today.empty and comp_tomm.empty:
        return pd.DataFrame()
    
    if not comp_today.empty:        
        comp_today['startdatetime'] = pd.to_datetime(comp_today['startdatetime'])
        index_names = comp_today[(comp_today['startdatetime'].dt.hour <= 14)].index
        comp_today = comp_today.drop(index_names)
        comp_today['startdatetimetype'] = 'AMC'

    if not comp_tomm.empty:
        comp_tomm['startdatetime'] = pd.to_datetime(comp_tomm['startdatetime'])
        index_names = comp_tomm[(comp_tomm['startdatetime'].dt.hour > 14)].index
        comp_tomm = comp_tomm.drop(index_names)
        comp_tomm['startdatetimetype'] = 'BMO'
        
    comp = pd.DataFrame()
    comp = pd.concat([comp_today, comp_tomm])
    comp = comp.drop(columns = ['gmtOffsetMilliSeconds', 'quoteType', 'epsactual', 'epssurprisepct'])
    comp = comp.drop_duplicates()
    comp.reset_index(drop=True, inplace=True)

    comp.insert(2, "stock_price", 0)
    comp.insert(3, "is_weekly", False)
    comp['volume'] = 0
    
    optionSet = get_stocks_with_options()
    weeklySet = get_stocks_with_weekly_options()
    for row in comp.iterrows():
        ticker = row[1].ticker
        if ticker not in optionSet:
            continue

        tk = yf.Ticker(ticker)
        exps = tk.options        
        if not exps: 
            continue

        e = exps[0]
        opt = tk.option_chain(e)
        volume_sum = opt.calls.volume.sum() + opt.puts.volume.sum()
        
        if volume_sum < min_vol_sum:
            continue
            
        openInterestSum = opt.calls.openInterest.sum() + opt.puts.openInterest.sum()

        rowVal = comp.index[comp['ticker'] == ticker]
        comp.loc[rowVal, 'stock_price'] = round(tk.history(period='1d')['Close'][0] , 2)
        comp.loc[rowVal, 'volume'] = volume_sum
        comp.loc[rowVal, 'openInterest'] = openInterestSum
        comp.loc[rowVal, 'is_weekly'] = (ticker in weeklySet)    
        
        move = get_expected_move(ticker)
        comp.loc[rowVal, 'aggregate_move%'] = move[3] * 100

    index_names = comp[(comp['volume'] == 0) | (comp['stock_price'] <= min_stock_price)].index
    comp = comp.drop(index_names)

    comp.sort_values(by=['volume'], inplace=True, ascending=False)
    comp.reset_index(drop=True, inplace=True)

    return comp


# print_full(get_companies_with_earnings_today_AMC_or_tomm_BMO())
def get_IV_crush_for_puts():
    """ Calculuate Previous day's IV crush"""
    
    dir = os.path.join(str(date.today().year), str(date.today() + timedelta(-1)))

    if not os.path.exists(dir):
        print("Directory does not exist for IV Crush Calculations")
        return
    
    num_files = len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])

    for x in range(num_files - 1):
        list_companies = pd.read_csv(os.path.join(dir, "companies.csv"))
        tickers = list_companies[['ticker', 'stock_price']]

        company = pd.read_csv(os.path.join(dir, tickers['ticker'][x] + '.csv'))
        df = get_put_option_chain(tickers['ticker'][x], tickers['stock_price'][x])[['strike','impliedVolatility']]
        # Calculuate IV for ATM and feasible OTM options
        ls = company[company['%probability_not_called'] != 100]['impliedVolatility']
        company['IV_crush'] = (df['impliedVolatility'] - ls)/ ls
        company['nextday_impliedVolatility'] = df['impliedVolatility']
        avg = company['IV_crush'].mean()
        company.loc['Average'] = {'IV_crush': avg}
        
        company.to_csv(os.path.join(dir, tickers['ticker'][x] + '.csv'), index=False)


