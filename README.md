# Earnings Strategies and Stock Data

This package shows multiple data for stocks nearing earnings like expected move of a stock, historical earnings effect, the Gaussian probability of an option being assigned and etc. This package is meant to allow traders to conveniently formulate the best strategies for any stock with earnings every day.

Check Today function outputs to HTML files that contains necessary information such as the list of companies with earnings, option chain, and historical earnings effect to help trade earning's stocks for that day. 

## Common Strategies 

### Expected Move > Earning's Effect Estimate

- Gain from Gamma Crush
- Selling CSP
- Selling Straddles and Strangles
- Iron Condor or Butterfly

### Expected Move < Earning's Effect Estimate even accomdating Gamma Risk

- Buying Lowly Valued Options
- Buying Spreads

<br></br>

## Quick Start

<strong> Functions return pandas DataFrame unless specified elsewise </strong>

```python
import earningstrats as es

""" 
Returns tuple of today AMC and tomorrow BMO companies' put option chain and historical earnings price effect
Change days_added to shift day by that much. Customize minimum volume sum and stock price
[0] - OTM Put option Chain
[1] - Historical earnings price effect = Change period to change how far back historical price effect shows
Outputs to today_companies.html, today_options.html, today_price_effect.html
"""
es.check_today(period = "5y", day_shift = 0, min_vol_sum = 3000, min_stock_price = 10)


"""
Get a stock's historical earnings price effect. Calculates earnings effect from market close -> next day open and next day close
Change period to change how far back historical price effect shows
"""
es.get_stock_earnings_price_effect(symbol, period = "5y")


"""
Get all the stocks with earnings today AMC or tomorrow BMO
"""
es.get_companies_with_earnings_today_AMC_or_tomm_BMO(day_shift = 0, min_vol_sum = 3000, min_stock_price = 10):


"""
Get Expected Move for a stock for the earliest option deadline. Returns tuple
[0] - IV Expected Move
[1] - ATM Straddle Expected Move
[2] - ATM Straddle + 1st Strangle Expected Move
[3] - Aggregate Estimate of Stock Expected Move (Used in calculations)
"""
es.get_expected_move(symbol)


"""
Gets the put option chain. Defaults to finding only OTM puts. Set price_ceiling to set cutoff 
Contains the Gaussian probability of option being assigned as well as the expected moves of a stock
"""
es.get_put_option_chain(symbol, price_ceiling = -1)



# Returns a set of stocks with weekly options
es.get_stocks_with_weekly_options()

# Returns a set of stocks with options
es.get_stocks_with_options()

# Get current stock price of stock
es.get_current_stock_price(symbol)

# Get days left until earliest option expiration
es.get_days_to_expiration(symbol)

# Get the earliest expiration option chain
es.get_earliest_deadline_options_chain(symbol)

# Get the entire put option chain
es.get_all_put_options(symbol)
```


## License

earningstrats is distributed under the Apache Software License. See the LICENSE file in the release for details

