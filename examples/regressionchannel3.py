import backtrader as bt

import numpy as np

import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from statsmodels.tools.eval_measures import rmse


def run_ordinary_least_squares(ols_dates, ols_data, statsmodels_settings):
    """
    This method receives the dates and prices of a data-set as well as settings for the StatsModels package,
    it then calculates the regression lines and / or the confidence lines are returns the objects
    """
    intercept = np.column_stack((ols_dates, ols_dates ** statsmodels_settings.exponent))
    constant = sm.add_constant(intercept)
    statsmodel_regression = sm.OLS(ols_data, constant).fit()
    # print(statsmodel_regression.summary())
    if statsmodels_settings.confidence:
        prstd, lower, upper = wls_prediction_std(statsmodel_regression)
        return statsmodel_regression, lower, upper
    else:
        return statsmodel_regression


class StatsModelsSettings:
    """
    This class contains settings for the statsmodels package, settings include,
    * exponent:int - when equal to one this is a straight line, when >1 this is a curve
    * confidence:boolean - specifies whether confidence lines should be calculated and plotted
    """

    exponent = 1
    confidence = False

    def __init__(self, exponent=1, confidence=False):
        """
        This initialization method constructs a new StatsModelSettings object
        """
        self.exponent = exponent
        self.confidence = confidence
        pass


class LinearRegression(bt.Indicator):
    lines = (
        "linear_regression",
        "s1h",
        "s1l",
        "s2h",
        "s2l",
        "s1hlr",
        "s1llr",
        "s2hlr",
        "s2llr",
        "slope",
        "sigma1",
        "sigma2",
        "rmseh",
        "rmsel",
        "rmseu",
    )
    params = (
        ("len", 21),
        ("tick", None),
    )

    stds = []

    last_lencount = 0

    plotlines = dict(linear_regression=dict(ls="--"))
    plotinfo = dict(subplot=True, plotlinelabels=True, plot=True)

    def __init__(self):
        self.addminperiod(self.params.len)

    # https://realpython.com/linear-regression-in-python/
    def next(self):
        if self.last_lencount < self.lines.linear_regression.lencount:
            self.last_lencount = self.lines.linear_regression.lencount

            raw_prices = self.data.close.get(size=self.params.len)

            prices = np.array(raw_prices)

            dates = np.array([i for i in range(0, self.params.len)])

            statsmodels_settings = StatsModelsSettings(1, True)

            # Only calculate and return confidence lines if setting = True
            if statsmodels_settings.confidence:
                regression, lower, upper = run_ordinary_least_squares(dates, prices, statsmodels_settings)
            else:
                regression = run_ordinary_least_squares(dates, prices, statsmodels_settings)

            std = np.std(prices)
            self.stds.append(std)

            stdFactor = 2

            self.lines.linear_regression[0] = regression.fittedvalues[-1]
            self.lines.s1h[0] = regression.fittedvalues[-1] + std
            self.lines.s1l[0] = regression.fittedvalues[-1] - std
            self.lines.s2h[0] = regression.fittedvalues[-1] + std * stdFactor
            self.lines.s2l[0] = regression.fittedvalues[-1] - std * stdFactor

            aaa = [i for i in regression.fittedvalues - std * stdFactor]
            rrr1, l2, u2 = run_ordinary_least_squares(dates, aaa, statsmodels_settings)
            p3 = rrr1.fittedvalues[-1]

            aaa = [i for i in regression.fittedvalues + std * stdFactor]
            rrr2, l2, u2 = run_ordinary_least_squares(dates, aaa, statsmodels_settings)
            p4 = rrr2.fittedvalues[-1]

            # self.lines.s2hlr[0] = p4
            # self.lines.s2llr[0] = p3

            self.lines.slope[0] = regression.params[1]
            # self.lines.sigma1[0] = std
            # self.lines.sigma2[0] = std * stdFactor

            # _rmseh = rmse(prices, rrr2.fittedvalues, axis=0)
            # _rmsel = rmse(prices, rrr1.fittedvalues, axis=0)
            # print(_rmseh, _rmsel)
            # self.lines.rmseh[0] = _rmseh.item()
            # self.lines.rmsel[0] = _rmsel.item()
            # self.lines.rmseu[0] = np.sign(_rmsel - _rmseh)
            # print(self.lines.rmseu[0])
