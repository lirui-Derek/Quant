"""回测主程序：负责串联数据层、策略层并执行回测。"""

import datetime
import backtrader as bt
import tushare as ts
from config.backtest_config import BACKTEST_CONFIG
from data.fetch_data import get_tushare_daily_data
from strategy.macd import MACDStrategy
from strategy.all_in_sizer import AllInSizer
from strategy.test_strategy import TestStrategy
from strategy.movingAvgCrossover import MovingAvgCrossover
from data.fetch_data import get_stock_name

# Backtrader 回测流程总结：
# 1. 数据层：从 Tushare 获取历史数据
# 2. 数据层：将数据整理成 Backtrader 可识别的格式
# 3. 策略层：定义交易逻辑（这里仅展示走势）
# 4. 回测主程序：创建 Cerebro 并绑定策略
# 5. 回测主程序：设置资金、手续费与运行参数
# 6. 回测主程序：执行回测并绘制图表


def main():
    """回测入口函数：读取数据、配置、运行策略并输出结果。"""
    # 1) 从配置文件读取参数
    config = BACKTEST_CONFIG
    ts_code = config["symbol"]
    stock_name = get_stock_name(ts_code)
    print(f"回测股票: {stock_name} ({ts_code})")
    
    start_date = config["start_date"]
    end_date = config["end_date"]

    # 2) 从数据层获取行情数据
    df = get_tushare_daily_data(ts_code, start_date, end_date)
    if df is None or df.empty:
        print(f"无法获取 {ts_code} 的数据")
        return
    
    # 3) 指定回测区间（用于图表展示）
    from_date = datetime.datetime.strptime(config["from_date"], "%Y-%m-%d")
    to_date = datetime.datetime.strptime(config["to_date"], "%Y-%m-%d")

    # 4) 创建 Backtrader 主引擎
    cerebro = bt.Cerebro()
    
    # 使用全仓 sizer：每次买入使用全部可用资金
    # cerebro.addsizer(AllInSizer)
    
    strategy_params = {
        "stop_loss": config["stop_loss"],
        "take_profit": config["take_profit"],
    }
    
    cerebro.addstrategy(MovingAvgCrossover)

    # 5) 将 DataFrame 转换为 Backtrader 数据源
    data = bt.feeds.PandasData(
        dataname=df,
        fromdate=from_date,
        todate=to_date,
        datetime=None,
        open="open",
        high="high",
        low="low",
        close="close",
        volume="vol",
        openinterest="openinterest",
    )
    cerebro.adddata(data, name=ts_code)

    # 6) 设置回测资金、手续费和滑点
    cerebro.broker.setcash(config["initial_cash"])
    cerebro.broker.setcommission(commission=config["commission"])
    cerebro.broker.set_slippage_perc(config["slippage"])

    # 7) 运行回测
    cerebro.run()

    print(f"初始资金: {config['initial_cash']}")
    print(f"回测结束资金: {cerebro.broker.getvalue()}")
    
    # 8) 绘制走势图（如果配置允许）
    if config["plot"]:
        cerebro.plot(volume=config["plot_volume"], style=config["plot_style"])


if __name__ == "__main__":
    main()
