# chartink_queries.py

# Chartink Queries to scan stocks 

GOLDEN_CROSS_OVER_DAILY = {"scan_clause" : "( {cash} ( latest sma( latest close , 50 ) > latest sma( latest close , 200 ) and 1 day ago  sma( latest close , 50 )<= 1 day ago  sma( latest close , 200 ) and 1 day ago sma( latest close , 50 ) <= 1 day ago sma( latest close , 200 ) and latest volume > 50000 ) )"}


MONTHLY_SWING_RSI_60_QUERY = {"scan_clause" : "( {46553} ( monthly high > 1 month ago high and 1 month ago high > 2 months ago high and 2 months ago high > 3 months ago high and monthly low > 1 month ago low and 1 month ago low > 2 months ago low and 2 months ago low > 3 months ago low and monthly close > 1 month ago close and 1 month ago close > 2 months ago close and 2 months ago close > 3 months ago close and monthly close > monthly high * 0.618 and latest rsi( 14 ) > 60 ) )"}


MONTHLY_SWING_QUERY = {"scan_clause" : "( {57960} ( monthly high > 1 month ago high and 1 month ago high > 2 months ago high and 2 months ago high > 3 months ago high and monthly low > 1 month ago low and 1 month ago low > 2 months ago low and 2 months ago low > 3 months ago low and monthly close > 1 month ago close and 1 month ago close > 2 months ago close and 2 months ago close > 3 months ago close and monthly close > monthly high * 0.618 ) )"}


OPEN_LOW_SAME_QUERY = {"scan_clause" : "( {57960} ( latest open = latest low and latest open > 1 day ago close * 1.01 and latest close >= ( latest open * 1.01 ) ) )"}


BUY_INTRADAY_QUERY = {"scan_clause" : "( {57960} ( ( latest high - latest low ) > ( 1 day ago high - 1 day ago low ) and( latest high - latest low ) > ( 2 days ago high - 2 days ago low ) and( latest high - latest low ) > ( 3 days ago high - 3 days ago low ) and( latest high - latest low ) > ( 4 days ago high - 4 days ago low ) and( latest high - latest low ) > ( 5 days ago high - 5 days ago low ) and( latest high - latest low ) > ( 6 days ago high - 6 days ago low ) and( latest high - latest low ) > ( 7 days ago high - 7 days ago low ) and latest close > latest open and latest close > 1 day ago close and weekly close > weekly open and monthly close > monthly open and latest sma( close,20 ) > latest sma( close,50 ) and latest sma( close,50 ) > latest sma( close,200 ) ) )"}


BUY_GOLDEN_RATIO = {"scan_clause" : "( {33489} ( [0] 5 minute close > ( ( ( ( 1 day ago high - 1 day ago low ) + [=1] 10 minute high - [=1] 10 minute low ) * 0.618 ) + 1 day ago close ) and [=1] 5 minute open < ( ( ( ( 1 day ago high - 1 day ago low ) + [=1] 10 minute high - [=1] 10 minute low ) * 0.236 ) + 1 day ago close ) ) )"}


SELL_GOLDEN_RATIO = {"scan_clause" : "( {33489} ( [0] 5 minute close < ( ( ( ( 1 day ago high - 1 day ago low ) + [=1] 10 minute high - [=1] 10 minute low ) * 0.618 ) - 1 day ago close ) * -1 and [=1] 5 minute open > ( ( ( ( 1 day ago high - 1 day ago low ) + [=1] 10 minute high - [=1] 10 minute low ) * 0.236 ) - 1 day ago close ) * -1 ) )"}