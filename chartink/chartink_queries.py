# chartink_queries.py

# Chartink Queries to scan stocks 

MONTHLY_SWING_QUERY = {"scan_clause" : "( {57960} ( monthly high > 1 month ago high and 1 month ago high > 2 months ago high and 2 months ago high > 3 months ago high and monthly low > 1 month ago low and 1 month ago low > 2 months ago low and 2 months ago low > 3 months ago low and monthly close > 1 month ago close and 1 month ago close > 2 months ago close and 2 months ago close > 3 months ago close and monthly close > monthly high * 0.618 and latest rsi( 14 ) > 50 and 1 day ago  rsi( 14 ) <= 50 ) )"}


OPEN_LOW_SAME_QUERY = {"scan_clause" : "( {57960} ( latest open = latest low and latest volume > 50000 and latest close < 5000 and latest avg true range( 14 ) < latest true range( 1 ) ) )"}


BUY_INTRADAY_QUERY = {"scan_clause" : "( {1090585} ( ( latest high - latest low ) > ( 1 day ago high - 1 day ago low ) and( latest high - latest low ) > ( 2 days ago high - 2 days ago low ) and( latest high - latest low ) > ( 3 days ago high - 3 days ago low ) and( latest high - latest low ) > ( 4 days ago high - 4 days ago low ) and( latest high - latest low ) > ( 5 days ago high - 5 days ago low ) and( latest high - latest low ) > ( 6 days ago high - 6 days ago low ) and( latest high - latest low ) > ( 7 days ago high - 7 days ago low ) and latest close > latest open and latest close > 1 day ago close and weekly close > weekly open and monthly close > monthly open and latest sma( close,20 ) > latest sma( close,50 ) and latest sma( close,50 ) > latest sma( close,200 ) ) )"}