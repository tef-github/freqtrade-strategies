# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import numpy as np
import freqtrade.vendor.qtpylib.indicators as qtpylib
import datetime
from technical.util import resample_to_interval, resampled_merge
from datetime import datetime, timedelta
from freqtrade.persistence import Trade
from freqtrade.strategy import stoploss_from_open, merge_informative_pair, DecimalParameter, IntParameter, CategoricalParameter

#author @tirail

class SMAOffset(IStrategy):
    INTERFACE_VERSION = 2

    base_nb_candles_buy = IntParameter(10, 30, default=30, space='buy')
    base_nb_candles_sell = IntParameter(10, 30, default=30, space='sell')
    low_offset = DecimalParameter(0.94, 0.98, default=0.97, space='buy')
    high_offset = DecimalParameter(1.01, 1.1, default=1.01, space='sell')
    buy_trigger = CategoricalParameter(['EMA', 'SMA'], default='SMA', space='buy')
    sell_trigger = CategoricalParameter(['EMA', 'SMA'], default='SMA', space='sell')

    # ROI table:
    minimal_roi = {
        "0": 1,
    }

    # Stoploss:
    stoploss = -0.5

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.1
    trailing_stop_positive_offset = 0
    trailing_only_offset_is_reached = False

    # Optimal timeframe for the strategy
    timeframe = '5m'

    use_sell_signal = True
    sell_profit_only = False

    process_only_new_candles = True
    startup_candle_count = 30

    plot_config = {
        'main_plot': {
            'ma_offset_buy': {'color': 'orange'},
            'ma_offset_sell': {'color': 'orange'},
        },
    }

    use_custom_stoploss = False


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if self.buy_trigger.value == 'EMA':
            dataframe['ma_buy'] = ta.EMA(dataframe, timeperiod=self.base_nb_candles_buy.value)
        else:
            dataframe['ma_buy'] = ta.SMA(dataframe, timeperiod=self.base_nb_candles_buy.value)

        if self.sell_trigger.value == 'EMA':
            dataframe['ma_sell'] = ta.EMA(dataframe, timeperiod=self.base_nb_candles_sell.value)
        else:
            dataframe['ma_sell'] = ta.SMA(dataframe, timeperiod=self.base_nb_candles_sell.value)

        dataframe['ma_offset_buy'] = dataframe['ma_buy'] * self.low_offset.value
        dataframe['ma_offset_sell'] = dataframe['ma_sell'] * self.high_offset.value

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['ma_buy'] * self.low_offset.value) &
                (dataframe['volume'] > 0)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['ma_sell'] * self.high_offset.value) &
                (dataframe['volume'] > 0)
            ),
            'sell'] = 1
        return dataframe
