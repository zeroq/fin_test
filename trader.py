from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime
import os.path
import sys

import backtrader as bt
import backtrader.indicators as btind

class PriceChannels(bt.Indicator):
    lines = ('pcl', 'pch', 'hhpc', 'llpc')
    params = (('period', 5),)

    def __init__(self):
        self.hhpc_modified = False
        self.addminperiod(self.params.period)

    def next(self):
        t1 = self.data.low[-1]
        t2 = self.data.low[-2]
        t3 = self.data.low[-3]
        t4 = self.data.low[-4]
        t5 = self.data.low[-5]
        self.lines.pcl[0] = min(t1, t2, t3, t4, t5)
        t1 = self.data.high[-1]
        t2 = self.data.high[-2]
        t3 = self.data.high[-3]
        t4 = self.data.high[-4]
        t5 = self.data.high[-5]
        self.lines.pch[0] = max(t1, t2, t3, t4, t5)

        if (self.data.high[0] > self.lines.pch[0]) and not self.hhpc_modified:
            self.lines.hhpc[0] = self.lines.pch[0]
            self.lines.llpc[0] = self.lines.llpc[-1]
            self.hhpc_modified = True
            return
        if (self.data.low[0] < self.lines.pcl[0]) and self.hhpc_modified:
            self.lines.llpc[0] = self.lines.pcl[0]
            self.lines.hhpc[0] = self.lines.hhpc[-1]
            self.hhpc_modified = False
            return

        self.lines.llpc[0] = self.lines.llpc[-1]
        self.lines.hhpc[0] = self.lines.hhpc[-1]
        return

# Price Channel Strategy
class PriceChannelStrategy(bt.Strategy):
    def __init__(self):
        pcl = PriceChannels(subplot=False)

        # TODO: add buy/sell strategy

# Test Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        # Only one order at a time
        if self.order:
            return
        if not self.position:
            # current close less than previous close
            if self.dataclose[0] < self.dataclose[-1]:
                # previous close less than the previous close
                if self.dataclose[-1] < self.dataclose[-2]:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order = self.buy()
        else:
            if len(self) >= (self.bar_executed + 5):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()

if __name__ == '__main__':
    # Init backtrader engine
    cerebro = bt.Cerebro()
    # set initial trading cash
    cerebro.broker.setcash(100000.0)

    # Add our strategy
    cerebro.addstrategy(PriceChannelStrategy)

    # Load data
    datapath = os.path.join('.', 'orcl-1995-2014.txt')

    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2000, 12, 31),
        reverse=False)

    # Add the data feed
    cerebro.adddata(data)

    # 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Run our stragey and plot the results
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot(style='candlestick', numfigs=1, volume=False)
