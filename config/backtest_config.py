"""回测配置文件：统一管理数据、资金、手续费和策略参数。"""

from datetime import datetime

# 动态生成当天日期，避免手动修改配置文件中的日期
TODAY = datetime.now()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
TODAY_STR_NO_SEP = TODAY.strftime("%Y%m%d")

BACKTEST_CONFIG = {
    # =========================
    # 基本交易设置
    # =========================
    "symbol": "600519.SH",
    "start_date": "20240101",
    "end_date": TODAY_STR_NO_SEP,

    # =========================
    # 资金与仓位设置
    # =========================
    "initial_cash": 100000.0,
    "stake": 100,
    "max_position": None,

    # =========================
    # 手续费与滑点
    # =========================
    "commission": 0.0005, 
    "slippage": 0.0005,
    "tax": 0.001,

    # =========================
    # 回测时间设置
    # =========================
    "from_date": "2022-01-01",
    "to_date": TODAY_STR,

    # =========================
    # 数据设置
    # =========================
    "data_frequency": "daily",
    "adjustment": "qfq",
    "required_columns": ["open", "high", "low", "close", "vol"],

    # =========================
    # 风险控制
    # =========================
    "stop_loss": 0.10,
    "take_profit": 0.20,
    "max_daily_loss": None,

    # =========================
    # 策略参数
    # =========================
    

    # =========================
    # 输出与展示
    # =========================
    "plot": True,
    "plot_volume": True,
    "plot_style": "candlestick", # line, candlestick, bar, ohlc
}
