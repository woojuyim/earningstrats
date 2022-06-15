import yfinance as yf
from scipy.stats import halfnorm
import pandas as pd
import math
from datetime import datetime, timedelta, date
pd.options.display.float_format = '{:.4f}'.format


def get_current_stock_price(symbol):
    tk = yf.Ticker(symbol)
    return tk.history(period='1d')['Close'][0]

def get_days_to_expiration(symbol):
    tk = yf.Ticker(symbol)
    exps = tk.options
    e = exps[0]
    dt_obj = datetime.strptime(e, '%Y-%m-%d')
    days_left = abs((datetime.now() - dt_obj).days)
    return days_left

def get_earliest_deadline_options_chain(symbol):
    """ Get call and put options for earliest deadline
    """
    tk = yf.Ticker(symbol)
    exps = tk.options
    options = pd.DataFrame()
    e = exps[0] 

    opt = tk.option_chain(e)
    calls = pd.DataFrame(opt.calls)
    puts = pd.DataFrame(opt.puts)
    calls['expirationDate'] = e
    puts['expirationDate'] = e
    
    options = pd.concat([options, calls])
    options = pd.concat([options, puts])
    
    options['isCall'] = options['contractSymbol'].str[4:].apply(lambda x: "C" in x)
    options[['bid', 'ask', 'strike']] = options[['bid', 'ask', 'strike']].apply(pd.to_numeric)
    options['mark'] = (options['bid'] + options['ask']) / 2
    options = options.drop(columns = ['contractSize', 'currency', 'change', 'percentChange', 'lastTradeDate'])
    
    return options

def get_expected_move(symbol):
    """Get Expected Move for a stock for the earliest option deadline. Returns tuple
    [0] - IV Expected Move
    [1] - ATM Straddle Expected Move
    [2] - ATM Straddle + 1st Strangle Expected Move
    [3] - Aggregate Estimate of Stock Expected Move (Used in calculations)
    """
    stock = yf.Ticker(symbol)
    curr = stock.history(period='1d')['Close'][0]
    options = get_earliest_deadline_options_chain(symbol)
        
    test_list = list(set(options.strike))
    temp = sorted(test_list, key=lambda x:abs(x-curr))
    if len(temp) < 3:
        return "Error"
    
    minVal = temp[0]
    higherVal = temp[1] if temp[1] > temp[2] else temp[2]
    lowerVal = temp[2] if temp[1] > temp[2] else temp[1]
    
    strad = options.loc[options.strike == minVal]
    low_stran = options.loc[options.strike == lowerVal]
    high_stran = options.loc[options.strike == higherVal]
    
    # IV Expected Move = Stock Price x (Implied Volatility / 100) x square root of (Days to Expiration / 365)
    expected_move = curr * strad.impliedVolatility * math.sqrt(get_days_to_expiration(symbol)/365)
    per = expected_move / curr
    
    straddle_sum = 0
    if len(strad.mark) == 2:
        straddle_sum = strad.mark.sum()
    elif len(strad.mark) == 1:
        straddle_sum = strad.mark.sum() * 2

    strangle_sum = 0
    high_mark = high_stran.loc[high_stran.isCall == True].mark
    low_mark = low_stran.loc[low_stran.isCall == False].mark
    if not high_mark.empty and not low_mark.empty:
        strangle_sum = high_mark.iloc[0] + low_mark.iloc[0]
    
    # If mark price or bid/ask price is 0, use last price to calculuate straddle and strangle Move
    if straddle_sum == 0:
        if len(strad.lastPrice) == 2:
            straddle_sum = strad.lastPrice.sum()
        elif len(strad.lastPrice) == 1:
            straddle_sum = strad.lastPrice.sum() * 2
    if strangle_sum == 0:
        high_last = high_stran.loc[high_stran.isCall == True].lastPrice
        low_last = low_stran.loc[low_stran.isCall == False].lastPrice
        if not high_last.empty and not low_last.empty:
            strangle_sum = high_last.iloc[0] + low_last.iloc[0]

    # Straddle Expected Move = 70% of ATM straddle + 30% of 1st Strangle
    total = 0.7 * (straddle_sum) + 0.3 * (strangle_sum)
    
    
    # If IV Move is too low, only straddle move
    avg = (per.mean() + (straddle_sum / curr)) / 2
    if(per.mean() <= 0.01):
        avg = straddle_sum / curr
    
    # IV Expected, ATM Straddle, ATM Straddle + 1st Strangle, Avg of IV + ATM
    return (per.mean(), straddle_sum / curr, total / curr, avg)

def get_put_option_chain(symbol, price_ceiling = -1):
    """ Gets the put option chain. Defaults to finding only OTM puts. Set price_ceiling to set cutoff 
    """
    tk = yf.Ticker(symbol)
    exps = tk.options
    e = exps[0] 

    opt = tk.option_chain(e)
    puts = pd.DataFrame(opt.puts)
    
    curr_price = tk.history(period='1d')['Close'][0]

    puts[['bid', 'ask', 'strike']] = puts[['bid', 'ask', 'strike']].apply(pd.to_numeric)
    puts.insert(6, 'mark', (puts['bid'] + puts['ask']) / 2)
    puts.insert(12, 'dist_to_stock%', abs(((curr_price - puts['strike'] ) / curr_price) * 100))
    puts = puts.drop(columns = ['contractSize', 'currency', 'change', 'percentChange', 'lastTradeDate', 'inTheMoney'])
    
    moves = get_expected_move(symbol)
    puts['aggregate_move%'] = moves[3] * 100
    puts['IV_move%'] = moves[0] * 100
    puts['straddle_move%'] = moves[1] * 100
    puts['strad_strang_move%'] = moves[2] * 100
    puts['expirationDate'] = e
    
    if price_ceiling == -1:
        price_ceiling = curr_price
    
    index_names = puts[(puts['strike'] > price_ceiling)].index
    puts = puts.drop(index_names)    
    
    zscore = (puts['dist_to_stock%'] / puts['aggregate_move%']) 
    puts.insert(6, '%probability_not_called', (halfnorm.cdf(zscore) * 100).round(4))
    collateral = puts['mark'] * 100
    if(collateral.all() == 0):
        collateral = puts['lastPrice'] * 100
    puts.insert(7, '%gain_of_collateral', (collateral * 100 / puts['strike']))    
    
    puts.sort_values(by=['strike'], inplace=True, ascending=False)
    puts.reset_index(drop=True, inplace=True)
    return puts

def get_all_put_options(symbol):
    tk = yf.Ticker(symbol)
    exps = tk.options
    e = exps[0] 

    opt = tk.option_chain(e)
    puts = pd.DataFrame(opt.puts)
    
    curr_price = tk.history(period='1d')['Close'][0]

    puts[['bid', 'ask', 'strike']] = puts[['bid', 'ask', 'strike']].apply(pd.to_numeric)
    puts.insert(6, 'mark', (puts['bid'] + puts['ask']) / 2)
    puts.insert(12, 'dist_to_stock%', abs(((curr_price - puts['strike'] ) / curr_price) * 100))
    
    puts = puts.drop(columns = ['contractSize', 'currency', 'change', 'percentChange', 'lastTradeDate'])

    
    moves = get_expected_move(symbol)
    puts['aggregate_move%'] = moves[3] * 100
    puts['IV_move%'] = moves[0] * 100
    puts['straddle_move%'] = moves[1] * 100
    puts['strad_strang_move%'] = moves[2] * 100
    
    puts['expirationDate'] = e
     
    puts.sort_values(by=['strike'], inplace=True, ascending=False)
    puts.reset_index(drop=True, inplace=True)
    
    zscore = (puts['dist_to_stock%'] / puts['aggregate_move%']) 
    puts.insert(6, '%probability_not_called', (halfnorm.cdf(zscore) * 100).round(4))
    collateral = puts['mark'] * 100
    if(collateral.all() == 0):
        collateral = puts['lastPrice'] * 100
        
    puts.insert(7, '%gain_of_collateral', (collateral * 100 / puts['strike']))   
    return puts
