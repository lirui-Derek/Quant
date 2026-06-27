"""数据层：负责从 Tushare 拉取并整理行情数据。"""

import pandas as pd
import tushare as ts

from data.data_quality_check import check_dataframe_quality, print_quality_summary

def get_stock_name(ts_code):
    """根据 ts_code 获取股票名称，失败时返回原代码。"""
    try:
        pro = ts.pro_api()
        df = pro.query(
            "stock_basic",
            exchange="",
            list_status="L",
            fields="ts_code,name",
        )
        if df is not None and not df.empty:
            match = df[df["ts_code"] == ts_code]
            if not match.empty:
                return match.iloc[0]["name"]
    except Exception as exc:
        print(f"获取股票名称失败: {exc}")
    return ts_code

def get_tushare_daily_data(ts_code, start_date, end_date):
    """
    从 Tushare 获取股票日线数据，并转换为 Backtrader 可用格式。

    返回值:
        pandas.DataFrame: 包含 open/high/low/close/vol/openinterest 列
    """
    # 初始化 Tushare API
    pro = ts.pro_api()

    # 1) 拉取日线数据
    df = pro.daily(
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date,
    )

    # 2) 先做基础空值检查，避免后续处理报错
    if df is None or df.empty:
        print(f"{ts_code} 数据为空，跳过")
        return None

    # 3) 处理时间字段，确保日期列可用于索引
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    df = df.sort_values("trade_date")
    df = df.set_index("trade_date")

    # 4) 调用数据质量检查函数
    report = check_dataframe_quality(df, ts_code)

    # 5) 仅在质量检查失败时给出提示，避免静默跳过
    if report.get("empty"):
        print(f"{ts_code} 数据为空，跳过")
        return None

    if not report.get("has_required_columns", False):
        print(f"{ts_code} 缺少必要字段：{report.get('missing_columns', [])}")
        return None

    if report.get("invalid_price_rows", 0) > 0:
        print(
            f"{ts_code} 存在 {report['invalid_price_rows']} 条异常价格记录，"
            f"请检查数据质量"
        )

    # 6) 输出简要质量报告（可选，用于调试）
    print_quality_summary(report)

    # 7) 保留回测需要的字段，并补上 openinterest
    required_columns = ["open", "high", "low", "close", "vol"]
    df = df[required_columns].copy()
    df["openinterest"] = 0

    return df