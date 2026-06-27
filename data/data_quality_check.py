"""Tushare 数据质量检查清单与示例函数。

用于在回测前检查数据是否存在常见问题，避免因数据异常导致错误结果。
"""

import pandas as pd


def check_dataframe_quality(df: pd.DataFrame, ts_code: str = ""):
    """检查数据框是否满足回测基本要求。

    参数:
        df: 需要检查的 DataFrame
        ts_code: 股票代码（仅用于输出提示）

    返回:
        dict: 包含检查结果的字典
    """
    result = {
        "ts_code": ts_code,
        "rows": int(len(df)) if df is not None else 0,
        "columns": list(df.columns) if df is not None else [],
        "missing_values": {},
        "duplicate_dates": False,
        "invalid_price_rows": 0,
        "empty": False,
        "has_required_columns": True,
    }

    if df is None or df.empty:
        result["empty"] = True
        return result

    # 检查缺失值
    result["missing_values"] = df.isna().sum().to_dict()

    # 检查日期重复
    if "trade_date" in df.columns:
        result["duplicate_dates"] = df["trade_date"].duplicated().any()

    # 检查必需字段是否存在
    required_cols = ["open", "high", "low", "close", "vol"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        result["has_required_columns"] = False
        result["missing_columns"] = missing_cols

    # 检查价格逻辑异常（高低价关系）
    if all(col in df.columns for col in ["open", "high", "low", "close"]):
        invalid_mask = (
            (df["high"] < df["low"]) |
            (df["open"] <= 0) |
            (df["high"] <= 0) |
            (df["low"] <= 0) |
            (df["close"] <= 0)
        )
        result["invalid_price_rows"] = int(invalid_mask.sum())

    return result


def print_quality_summary(result: dict):
    """打印检查结果摘要。"""
    print(f"股票代码：{result.get('ts_code', '未知')}")
    print(f"总行数：{result.get('rows', 0)}")
    print(f"数据是否为空：{result.get('empty', False)}")
    print(f"是否有必需字段：{result.get('has_required_columns', False)}")
    print(f"日期是否重复：{result.get('duplicate_dates', False)}")
    print(f"异常价格记录数：{result.get('invalid_price_rows', 0)}")

    missing = result.get("missing_values", {})
    if missing:
        print("缺失值统计：")
        for k, v in missing.items():
            if v > 0:
                print(f"  - {k}: {v}")

    missing_cols = result.get("missing_columns", [])
    if missing_cols:
        print(f"缺失字段：{missing_cols}")


# 示例：如果你以后想在回测前直接调用，可以这么写
# df = get_tushare_daily_data("600850.SH", "20220101", "20260622")
# report = check_dataframe_quality(df, "600850.SH")
# print_quality_summary(report)