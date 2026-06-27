# -*- coding: utf-8 -*-
"""
Semi-auto paper trading entrypoint.

Flow:
    Tushare -> Backtrader signal engine -> CSV order checklist -> manual broker entry

Run after the market close. The script does not connect to a broker and does not
place real or simulated broker-side orders. It only produces a checklist for you
to type into a broker paper-trading account manually.

这是一个半自动化的纸面交易入口脚本：
1. 从 Tushare 拉取行情数据
2. 通过 Backtrader 计算买卖信号
3. 将信号写入 CSV，供用户手工在券商模拟账户中输入订单
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import backtrader as bt
import pandas as pd
from strategy.ManualMovingAverageSignal import ManualMovingAverageSignal

from config.backtest_config import BACKTEST_CONFIG
from data.fetch_data import get_stock_name, get_tushare_daily_data

# 输出文件路径：一个是当天手工交易计划，一个是历史信号记录
PLAN_FILE = Path("manual_trade_plan.csv")
HISTORY_FILE = Path("manual_trade_signal_history.csv")


def main() -> None:
    # 读取回测配置并生成观测股票名单
    config = BACKTEST_CONFIG
    watchlist = get_watchlist(config)
    all_signals: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []

    print("Semi-auto paper trading signal run")
    print(f"Watchlist: {', '.join(watchlist)}")

    for ts_code in watchlist:
        stock_name = get_stock_name(ts_code)
        df = get_tushare_daily_data(ts_code, config["start_date"], config["end_date"])
        if df is None or df.empty:
            plan_rows.append(build_hold_row(ts_code, stock_name, "No usable Tushare data."))
            continue

        signals = run_backtrader_signal_engine(ts_code, stock_name, df, config)
        all_signals.extend(signals)

        latest_date = df.index.max().date().isoformat()
        today_signals = [row for row in signals if row["signal_date"] == latest_date]
        if today_signals:
            plan_rows.extend(today_signals)
        else:
            last_close = float(df.iloc[-1]["close"])
            plan_rows.append(
                build_hold_row(
                    ts_code,
                    stock_name,
                    f"No new buy/sell signal on latest trading day {latest_date}.",
                    signal_date=latest_date,
                    reference_close=last_close,
                )
            )

    write_csv(PLAN_FILE, plan_rows)
    write_csv(HISTORY_FILE, all_signals)
    print_summary(plan_rows)


def get_watchlist(config: dict[str, Any]) -> list[str]:
    """从环境变量或配置读取观测股票列表，优先使用 WATCHLIST 覆盖默认设置。"""
    env_watchlist = os.getenv("WATCHLIST", "").strip()
    if env_watchlist:
        return [code.strip() for code in env_watchlist.split(",") if code.strip()]
    return [config["symbol"]]


def run_backtrader_signal_engine(
    ts_code: str,
    stock_name: str,
    df: pd.DataFrame,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """运行 Backtrader 策略引擎并返回当天生成的信号列表。"""

    signals: list[dict[str, Any]] = []

    # 创建 Cerebro 引擎并禁用默认统计输出
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addstrategy(
        ManualMovingAverageSignal,
        maperiod=int(config.get("ma_period", 20)),
        max_cash_fraction=float(config.get("max_cash_fraction", 0.5)),
        lot_size=int(config.get("lot_size", 100)),
        ts_code=ts_code,
        stock_name=stock_name,
        signals=signals,
    )

    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open="open",
        high="high",
        low="low",
        close="close",
        volume="vol",
        openinterest="openinterest",
    )
    cerebro.adddata(data, name=ts_code)
    cerebro.broker.setcash(float(config["initial_cash"]))
    cerebro.broker.setcommission(commission=float(config.get("commission", 0.0005)))
    cerebro.broker.set_slippage_perc(float(config.get("slippage", 0.0005)))
    cerebro.run()

    return signals


def build_hold_row(
    ts_code: str,
    stock_name: str,
    reason: str,
    signal_date: str = "",
    reference_close: float | None = None,
) -> dict[str, Any]:
    """生成一条 HOLD 行，表示当前无需手工下单。"""
    return {
        "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "signal_date": signal_date,
        "manual_action_date": "",
        "ts_code": ts_code,
        "stock_name": stock_name,
        "action": "HOLD",
        "suggested_shares": 0,
        "reference_close": round(reference_close, 4) if reference_close is not None else "",
        "sma": "",
        "cash_before_signal": "",
        "portfolio_value": "",
        "status": "no_manual_entry",
        "reason": reason,
        "manual_checklist": "No manual broker action needed.",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    # 将信号数据输出为 CSV 文件，方便手工下单和历史复盘
    columns = [
        "run_at",
        "signal_date",
        "manual_action_date",
        "ts_code",
        "stock_name",
        "action",
        "suggested_shares",
        "reference_close",
        "sma",
        "cash_before_signal",
        "portfolio_value",
        "status",
        "reason",
        "manual_checklist",
    ]
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Wrote {path.resolve()}")


def print_summary(plan_rows: list[dict[str, Any]]) -> None:
    actionable = [row for row in plan_rows if row["action"] in ("BUY", "SELL")]
    if not actionable:
        print("No manual order needed for the latest trading day.")
        return

    print("Manual orders to enter in broker paper account:")
    for row in actionable:
        print(
            f"- {row['action']} {row['ts_code']} {row['stock_name']} "
            f"{row['suggested_shares']} shares; reference close {row['reference_close']}"
        )


if __name__ == "__main__":
    main()
