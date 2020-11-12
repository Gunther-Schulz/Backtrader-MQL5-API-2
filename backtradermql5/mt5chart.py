from backtrader import bt
import math
import uuid


class MTraderChart(bt.Indicator):

    # Inherited Indicator class requires at least one line
    lines = ("dummyline",)
    plotlines = dict(dummyline=dict(_plotskip="True",))
    plotinfo = dict(plotskip=True)

    # Experimental
    params = dict(realtime=False)

    # Equates to constant EMPTY_VALUE in MQL5
    str_inf = "1.797693134862316e+308"

    def __init__(self):
        """
        Opens a chart window in MT5 withe the smybol and timeframe of the passed data stream object.
        """
        self.indicators = list()
        self.sub_window_count = 0

        # TODO implent drawing of chart objects
        # graphic_types = ["curve", "line", "arrowbuy", "arrowsell"]
        self.p.chart_id = str(uuid.uuid4())
        self.p.symbol = self.data._dataname
        self.p.timeframe = self.data._timeframe
        self.p.compression = self.data._compression

        # is a resampled datafeed
        if type(self.data).__name__ == "DataClone":
            self.p.d = self.data.p.dataname
            self.p.store = self.data.p.dataname.o
            self.resampled = True
        else:
            self.p.d = self.data
            self.p.store = self.data.o
            self.resampled = False

        res = self.p.store.config_chart(self.p.chart_id, self.p.symbol, self.p.timeframe, self.p.compression)
        self.p.mt_chart_id = res["mtChartId"]

    def next(self):
        state = self.p.d._state
        qsize = self.p.d._historyback_queue_size
        _ST_LIVE = self.p.d._ST_LIVE

        for indicator in self.indicators:
            for line in indicator.line_store:
                date = self.data.datetime.datetime()
                value = line["line"][0]
                if date != line["last_date"] and not math.isnan(value):
                    line["values"].append(round(value, 6))
                    line["from_date"] = date.timestamp()
                    if qsize <= 1 or state == _ST_LIVE or self.p.realtime:
                        if self.resampled and not (
                            self.p.d._timeframe == self.p.timeframe and self.p.d._compression == self.p.compression
                        ):
                            if line["last_date"]:
                                line["from_date"] = line["last_date"].timestamp()
                        line["values"].reverse()
                        self.p.store.push_chart_data(
                            self.p.chart_id,
                            self.p.mt_chart_id,
                            indicator.id,
                            line["buffer_id"],
                            line["from_date"],
                            line["values"],
                        )
                        line["values"] = []
                        line["from_date"] = None
                    line["last_date"] = date

    def addchartindicator(self, indicator):
        """
        Adds an indicator instance to a chart (sub)window in MT5.
        """
        if indicator.sub_window_idx > self.sub_window_count:
            self.sub_window_count += 1
            indicator.sub_window_idx = self.sub_window_count

        indicator.id = str(uuid.uuid4())

        self.p.store.chart_add_indicator(self.p.chart_id, indicator.id, indicator.sub_window_idx, indicator.shortname)
        for line in indicator.line_store:
            self.p.store.chart_indicator_add_line(self.p.chart_id, indicator.id, line["style"])
        self.indicators.append(indicator)


class ChartIndicator:
    """
    Chart indicator class
    """

    def __init__(self, idx, shortname):
        self.sub_window_idx = idx
        self.shortname = shortname
        self.id = None
        self.indicator_line_count = -1
        self.line_store = []

    def addline(self, line, *args, **kwargs):
        style = {
            "linelabel": "Value",
            "color": "clrYellow",
            "linetype": "DRAW_LINE",
            "linestyle": "STYLE_SOLID",
            "linewidth": 1,
            "blankforming": True,
        }
        style.update(**kwargs["style"])

        self.indicator_line_count += 1

        self.line_store.append(
            {
                "last_date": None,
                "from_date": None,
                "line": line,
                "style": style,
                "values": [],
                "buffer_id": self.indicator_line_count,
            }
        )
