
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mplfinance as mpf
import plotly.graph_objects as go
import sys

# SYMBOL,INTERVAL,DATE,OPEN,HIGH,LOW,CLOSE,VOLUME
my_headers = ['symbol', 'interval', 'date', 'open', 'high', 'low', 'close', 'volume']

# Read data CSV and apply my_headers above + index on date column
df = pd.read_csv('data.csv', index_col=2, parse_dates=True, header=1, names=my_headers)

# Price Channel High (exclude current with shift(1))
df['PCH'] = df['high'].shift(1).rolling(window=5).max()

# Price Channel Low (exclude current with shift(1))
df['PCL'] = df['low'].shift(1).rolling(window=5).min()

# Generate HHPC and LLPC Values
hhpc_mod = True
# iterate over data
for index, row in df.iterrows():
    loc = df.index.get_loc(index)
    prev = df.iloc[loc - 1]
    if (row['low'] < row['PCL']) and not hhpc_mod:
        df.at[index, 'HHPC'] = row['PCH']
        try:
            df.loc[index, 'LLPC'] = prev['LLPC']
        except KeyError:
            pass
        hhpc_mod = True
        continue
    if (row['high'] > row['PCH']) and hhpc_mod:
        df.at[index, 'LLPC'] = row['PCL']
        try:
            df.loc[index, 'HHPC'] = prev['HHPC']
        except KeyError:
            pass
        hhpc_mod = False
        continue
    try:
        df.loc[index, 'LLPC'] = df.loc[str(int(index) - 1), 'LLPC']
    except:
        pass
    try:
        df.loc[index, 'HHPC'] = prev['HHPC']
    except KeyError:
        pass
    try:
        df.loc[index, 'LLPC'] = prev['LLPC']
    except KeyError:
        pass

# Write results to CSV
df.to_csv('out.csv', index=True)

# Plot data as Candlesticks
fig = go.Figure(data=[go.Candlestick(x=df.index,
                                     open=df.open,
                                     high=df.high,
                                     low=df.low,
                                     close=df.close),
                      go.Scatter(x=df.index, y=df.PCH, line=dict(color='blue', width=1), name='Price Channel High'),
                      go.Scatter(x=df.index, y=df.PCL, line=dict(color='orange', width=1), name='Price Channel Low'),
                      go.Scatter(x=df.index, y=df.LLPC, line=dict(color='red', width=1), name='Lower Low Price Channel '),
                      go.Scatter(x=df.index, y=df.HHPC, line=dict(color='green', width=1), name='Higher High Price Channel '),
                ])

# Display results
fig.update_layout(xaxis_rangeslider_visible=False)
fig.show()
