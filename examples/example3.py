import pytz
import backtrader as bt
import backtrader.indicators as btind
from backtradermql5.mt5store import MTraderStore
from backtradermql5.mt5indicator import getMTraderIndicator
from backtradermql5.mt5chart import MTraderChart, ChartIndicator
from datetime import datetime, timedelta
from regressionchannel3 import LinearRegression
from ohlc import OHLC


class SmaCross(bt.SignalStrategy):
    def __init__(self, store):
        self.buy_order = None
        self.live_data = False

        # # Attach and retrieve values from the MT5 indicator "Examples/MACD"
        # self.mt5cma0 = getMTraderIndicator(
        #     # MTraderStorestore instance
        #     store,
        #     # Data feed to run the indicator calculations on
        #     self.datas[0],
        #     # Set accessor(s) for the indicator output lines
        #     ("cma",),
        #     # MT5 inidicator name
        #     indicator="Examples/Custom Moving Average",
        #     # Indicator parameters.
        #     #   Any omitted values will use the defaults as defind by the indicator.
        #     #   The parameter "params" must exist. If you want to use only the indicator defaults,
        #     #   pass an empty list: params=[],
        #     params=[13, 0, "MODE_SMMA"],
        # )()

        # Instantiating backtrader indicator Bollinger Bands and Moving Averages
        #   Important: This needs to come before instantiating a chart window
        #   with backtradermql5.mt5indicator.MTraderChart. Otherwise backtrader will fail.
        self.bb = btind.BollingerBands(self.datas[0])
        # self.bbM15 = btind.BollingerBands(self.datas[1])
        self.sma = btind.MovingAverageSimple(self.datas[0])
        # self.smaM15 = btind.MovingAverageSimple(self.datas[1])

        self.lr = LinearRegression(self.datas[0], len=21)
        # self.lr2 = LinearRegression(self.datas[1], len=21)

        self.ohlc = OHLC(self.datas[0], len=21)

        # Plot the backtrader BollingerBand and SMA indicators to a chart window in MT5

        def addChart(chart, bb, sma, lr, ohlc):
            # Instantiate new indicator and draw to the main window. The parameter idx=0 specifies wether to plot to the
            # main window (idx=0) or a subwindow (idx=1 for the first subwindow, idx=2 for the second etc.).
            indi0 = ChartIndicator(idx=0, shortname="Bollinger Bands")

            # # Add line buffers
            # indi0.addline(
            #     bb.top, style={"linelabel": "Top", "color": "clrBlue",},
            # )
            # indi0.addline(
            #     bb.mid, style={"linelabel": "Middle", "color": "clrYellow",},
            # )
            # indi0.addline(
            #     bb.bot, style={"linelabel": "Bottom", "color": "clrGreen",},
            # )
            indi0.addline(
                lr.linear_regression,
                style={"linelabel": "linear_regression", "color": "clrYellow", "linewidth": 3, "blankforming": True},
            )
            indi0.addline(
                ohlc.o, style={"linelabel": "open", "color": "clrRed", "linewidth": 1},
            )
            indi0.addline(
                ohlc.c, style={"linelabel": "close", "color": "clrRed", "linewidth": 1},
            )
            # Add the indicator to the chart and draw the line buffers.
            chart.addchartindicator(indi0)

            # # Instantiate second indicator to draw to the first sub-window and add line buffers
            # indi1 = ChartIndicator(idx=1, shortname="Simple Moving Average")
            # indi1.addline(
            #     sma.sma, style={"linelabel": "SMA", "color": "clrBlue", "linestyle": "STYLE_DASH", "linewidth": 2},
            # )
            # chart.addchartindicator(indi1)

        # Instantiate a new chart window and plot
        # chartM5 = MTraderChart(self.datas[0])
        # addChart(chartM5, self.bbM5, self.smaM5, self.lr1)

        # Instantiate a second chart window and plot
        # chartM15 = MTraderChart(self.datas[1], resampledfrom=self.datas[0])
        chart = MTraderChart(self.datas[0], realtime=True)
        addChart(chart, self.bb, self.sma, self.lr, self.ohlc)

    def next(self):
        # Uncomment below to execute trades
        # if self.buy_order is None:
        #     self.buy_order = self.buy_bracket(limitprice=1.13, stopprice=1.10, size=0.1, exectype=bt.Order.Market)

        if self.live_data:
            cash = self.broker.getcash()

            # Cancel order
            if self.buy_order is not None:
                self.cancel(self.buy_order[0])

        else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
            cash = "NA"

        for data in self.datas:
            print(
                f"{data.datetime.datetime()} - {data._name} | Cash {cash} | O: {data.open[0]} H: {data.high[0]} L: {data.low[0]} C: {data.close[0]} V:{data.volume[0]}"
            )
        print("")
        # print(self.datas[0]._historyback_queue_size)
        # print(f"MT5 indicator 'Examples/Custom Moving Average': {self.mt5cma.cma[0]}")  # " {self.mt5macd.macd[0]}")
        # print(f"MT5 indicator 'LR': {self.lr1.linear_regression[0]}")  # " {self.mt5macd.macd[0]}")

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = f"Data Status: {data._getstatusname(status)}"
        print(dt, dn, msg)
        if data._getstatusname(status) == "LIVE":
            self.live_data = True
        else:
            self.live_data = False


# If MetaTrader runs locally
# host = "localhost"
# If Metatrader runs at differnt address
host = "192.168.56.124"

store = MTraderStore(host=host, debug=False, datatimeout=10)

cerebro = bt.Cerebro()

cerebro.addstrategy(SmaCross, store)

broker = store.getbroker(use_positions=True)
cerebro.setbroker(broker)

start_date = datetime.now() - timedelta(hours=20)


def rTicks(historical=True, boundoff=0, rc=1):
    data = store.getdata(
        dataname="EURUSD",
        name="TICKS",
        timeframe=bt.TimeFrame.Ticks,
        fromdate=start_date,
        # todate=datetime(2020, 11, 13, 20, 50),
        compression=1,
        # useask=True, # For Tick data only: Ask price instead if the default bid price
        # addspread=True, # For Candle data only: Add the spread value
        # Specify the timezone of the trade server that MetaTrader connects to.
        # More information at: https://www.backtrader.com/docu/timemgmt/
        tz=pytz.timezone("UTC"),
        historical=historical,
        correct_tick_history=True,
    )
    run(data, boundoff, rc)


def rBars(historical=True, boundoff=1, rc=5):
    data = store.getdata(
        dataname="EURUSD",
        name="BARS",
        timeframe=bt.TimeFrame.Minutes,
        fromdate=start_date,
        compression=1,
        # useask=True, # For Tick data only: Ask price instead if the default bid price
        # addspread=True, # For Candle data only: Add the spread value
        tz=pytz.timezone("UTC"),
        historical=historical,
    )
    run(data, boundoff, rc)


def run(data=None, boundoff=None, rc=None):
    # cerebro.adddata(data)
    cerebro.resampledata(
        data,
        name="RESAMPLED",
        timeframe=bt.TimeFrame.Minutes,
        compression=rc,
        boundoff=boundoff,
        # rightedge=False,
        # adjbartime=False,
        # bar2edge=False,
    )
    # cerebro.replaydata(data, name="REPLAYED", timeframe=bt.TimeFrame.Minutes, compression=1)


start_date = datetime.now() - timedelta(hours=2)

### TODO !!! DONT FORGET TICKCORRECT IN  MT5
# --------------- Ticks
# Bars from Ticks are slightly different to MT5 bars, because the tick history apparently differs
# Solved in charts.py
# rTicks(historical=True, boundoff=0, rc=1)

# Only trigger on new resampled bar Solved by realtime switch
# TODO: Slight offset. Check exactly why. Probably different tick data
rTicks(historical=False, boundoff=0, rc=1)

# There seems to be not difference for both below
# rTicks(historical=True, boundoff=1, rc=1)
# rTicks(historical=True, boundoff=1, rc=5)

# rTicks(historical=True, boundoff=1, rc=1)
# rTicks(historical=False, boundoff=1, rc=1)

# ---------Bars
start_date = datetime.now() - timedelta(hours=6)

# rBars(historical=True, boundoff=1, rc=1)

# rBars(historical=True, boundoff=1, rc=5)

# rBars(historical=False, boundoff=1, rc=5)

# rBars(historical=True, boundoff=0, rc=1)
# rBars(historical=False, boundoff=0, rc=1)

# resampled is a combination of the tixks of the previous period. i.e. minute 52 uses all ticks of minute 51
# replay builds the bar in real-time.

# 1) When in live mode, indicators will display on the first live resampled bar
# TODO check above

# 2) Use boundoff=1 for MT5 behaviour
# https://www.backtrader.com/docu/data-resampling/data-resampling/
# boundoff=1 of does not work on the combination of ticks and historical=true

# No Boundoff for Ticks
# cerebro.resampledata(data0, name="RESAMPLED", timeframe=bt.TimeFrame.Minutes, compression=1)  # , boundoff=1)
# Always Boundoff if no Ticks
# cerebro.resampledata(data1, name="RESAMPLED", timeframe=bt.TimeFrame.Minutes, compression=1, boundoff=1)
# cerebro.replaydata(data0, name="REPLAYED", timeframe=bt.TimeFrame.Minutes, compression=1)


cerebro.run(stdstats=False)


# Ticks 10 pips UNterschied zu markets.com MT market watch
# Ticks 1 piepette unterschied zu live ticks (as they arrive) zu markets.com
