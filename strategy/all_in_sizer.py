"""全仓下单 sizer：每次买入使用当前全部可用资金（按收盘价计算手数）。"""

import backtrader as bt


class AllInSizer(bt.Sizer):
    params = ()

    def _getsizing(self, comminfo, cash, data, isbuy):
        # 仅在买入时计算手数；卖出由策略或引擎决定
        if not isbuy:
            return 0

        price = data.close[0]
        if price is None or price <= 0:
            return 0

        # 使用所有可用现金按当前价格计算可买入的整手数量
        size = int((cash / 2) / price)
        return size if size > 0 else 0
