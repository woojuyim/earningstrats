import pandas as pd
from datetime import date
import os
from earnings import *

def check_today(duration = "10y", days_added = 0):
    today_comp = get_companies_with_earnings_today_AMC_or_tomm_BMO(days_added)
    total = pd.DataFrame()
    price = pd.DataFrame()
    outdir = os.path.join(str(date.today().year), str(date.today()))

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

        price_effect = get_stock_earnings_price_effect(ticker, duration)
        price_effect.loc["Empty"] = '' 
        price_effect.loc["Space"] = '' 
        price = pd.concat([price, price_effect])   
    
    today_comp.to_html("today_companies.html")
    total.to_html('today_options.html')
    price.to_html('today_price_effect.html')
    get_IV_crush_for_puts()
    print("Done")
    
    return (total, price)

check_today("4y", 0)
