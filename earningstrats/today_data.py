import pandas as pd
from datetime import date
import os
from earningstrats.earnings import *

def check_today(period = "5y", day_shift = 0, min_vol_sum = 3000, min_stock_price = 10):
    """
    Returns tuple of today AMC and tomorrow BMO companies' put option chain and historical earnings price effect
    Change days_added to shift day by that much. Customize minimum volume sum and stock price
    [0] - OTM Put option Chain
    [1] - Historical earnings price effect = Change period to change how far back historical price effect shows
    Outputs to today_companies.html, today_options.html, today_price_effect.html
    """
    today_comp = get_companies_with_earnings_today_AMC_or_tomm_BMO(day_shift, min_vol_sum, min_stock_price)
    total = pd.DataFrame()
    price = pd.DataFrame()
    
    yearPath = os.path.join(str(date.today().year))
    if not os.path.exists(yearPath):
        os.mkdir(yearPath)
        
    outdir = os.path.join(yearPath, str(date.today()))
    
    for row in today_comp.iterrows():
        ticker = row[1].ticker
        temp = get_put_option_chain(ticker)

        if not os.path.exists(outdir):
            os.mkdir(outdir)

        fullname = os.path.join(outdir, ticker + ".csv")    
        temp.to_csv(fullname)
        
        today_path = os.path.join(outdir, "companies.csv")    
        today_comp.to_csv(today_path)

        total = pd.concat([total, temp], ignore_index=True)
        total.loc["Empty"] = '' 
        total.loc["Space"] = ''        

        price_effect = get_stock_earnings_price_effect(ticker, period)
        price_effect.loc["Empty"] = '' 
        price_effect.loc["Space"] = '' 
        price = pd.concat([price, price_effect])   
    
    today_comp.to_html("today_companies.html")
    total.to_html('today_options.html')
    price.to_html('today_price_effect.html')
    return (total, price)


if __name__ == "__main__":
    check_today(period = "3y", day_shift = 0, min_vol_sum = 500, min_stock_price = 10)
    # get_IV_crush_for_puts()    

