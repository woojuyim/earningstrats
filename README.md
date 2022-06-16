# Earnings Strategies and Stock Data

This package shows multiple data for stocks nearing earnings like its expected move, historical earnings effect, the Gaussian probability of an option being assigned, etc. This package allows traders to conveniently formulate the best strategies for any stock with earnings every day.

Check Today is the aggregate function that contain all the necessary information such as the list of companies with earnings, combined option chain, and historical earnings price effect to help trade stocks with earnings for that day. It pretty-prints its output to HTML files, allowing for a quick and convenient scan.

## Common Strategies 

### Expected Move > Earning's Effect Estimate

- Gain from Gamma Crush
- Selling CSP
- Selling Straddles and Strangles
- Iron Condor or Butterfly

### Expected Move < Earning's Effect Estimate even accommodating Gamma Risk

- Buying Undervalued Options
- Buying Spreads

<br></br>

## Quick Start

<strong> Functions return pandas DataFrame unless specified elsewise </strong>

### Today_Data

```python
import earningstrats.today_data as td

""" 
Returns tuple of today AMC and tomorrow BMO companies' put option chain and historical earnings price effect
Change days_added to shift day by that much. Customize minimum volume sum and stock price
[0] - OTM Put option Chain
[1] - Historical earnings price effect = Change period to change how far back historical price effect shows
Outputs to today_companies.html, today_options.html, today_price_effect.html
"""
td.check_today(period = "5y", day_shift = 0, min_vol_sum = 3000, min_stock_price = 10)

```
### Earnings

```python
import earningstrats.earnings as ea

"""
Get a stock's historical earnings price effect. Calculates earnings effect from market close -> next day open and next day close
Change period to change how far back historical price effect shows
"""
ea.get_stock_earnings_price_effect(symbol, period = "5y")


"""
Get all the stocks with earnings today AMC or tomorrow BMO
"""
ea.get_companies_with_earnings_today_AMC_or_tomm_BMO(day_shift = 0, min_vol_sum = 3000, min_stock_price = 10)

```

### Options

```python
import earningstrats.options as opd


"""
Get Expected Move for a stock for the earliest option deadline. Returns tuple
[0] - IV Expected Move
[1] - ATM Straddle Expected Move
[2] - ATM Straddle + 1st Strangle Expected Move
[3] - Aggregate Estimate of Stock Expected Move (Used in calculations)
"""
opd.get_expected_move(symbol)


"""
Gets the put option chain. Defaults to finding only OTM puts. Set price_ceiling to set cutoff 
Contains the Gaussian probability of option being assigned as well as the expected moves of a stock
"""
opd.get_put_option_chain(symbol, price_ceiling = -1)


# Get current stock price of stock
opd.get_current_stock_price(symbol)

# Get days left until earliest option expiration
opd.get_days_to_expiration(symbol)

# Get the earliest expiration option chain
opd.get_earliest_deadline_options_chain(symbol)

# Get the entire put option chain
opd.get_all_put_options(symbol)

```

### Option_Set
```python
import earningstrats.option_set as ops
# Returns a set of stocks with weekly options
ops.get_stocks_with_weekly_options()

# Returns a set of stocks with options
ops.get_stocks_with_options()

```

## License

earningstrats is distributed under the Apache Software License. See the LICENSE file in the release for details

