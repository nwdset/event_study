"""Generating Event Driven Returns.

	This script is used to generate event driven returns for a given
	long form signals.
"""
import lrl.data
import pandas as pd

from lrl.utils.timeutil import get_trading_date

from statsmodels.regression.rolling import RollingOLS

SPY = 147418


def get_returns(start, end, assetids, key="close"):
    assetids = list(set(assetids))
    prices = lrl.data.get_data(start, end, securities=assetids, keys=[key])
    returns = prices.unstack().pct_change()[1:]
    returns = returns.mask(returns.eq(0))
    returns = returns[key]
    return returns


def get_excess_returns(start, end, assetids):
    # get rolling 60 days of beta
    start = start - pd.Timedelta("61 Days")
    assetid_returns = get_returns(start, end, assetids)
    assetid_returns_copy = assetid_returns.add_prefix("assetid_")
    spy_returns = get_returns(start, end, [147418]).iloc[:, 0].rename("spy")
    # excess_returns = assetid_returns.sub(spy_returns, axis=0)

    # calculate beta for each assetid
    betas = []
    for col in assetid_returns_copy:
        beta = (
            RollingOLS.from_formula(
                f"{col} ~ spy + 1",
                pd.concat(
                    [assetid_returns_copy[col].fillna(spy_returns), spy_returns], axis=1
                ).dropna(),
                window=60,
            )
            .fit()
            .params["spy"]
            .rename(int(col.replace("assetid_", "")))
            .reindex(assetid_returns.index)
            .shift()
            .fillna(1)
        )
        betas.append(beta)
    betas = pd.concat(betas, axis=1)
    excess_returns = assetid_returns.sub(betas.mul(spy_returns, axis=0))

    return excess_returns


def post_event_returns(signal, returns, n=10):
    # push signal dates to nearest trading day
    signal["date"] = signal["date"].apply(get_trading_date)
    signal = signal.set_index(["date", "assetid"])
    signal = signal.loc[signal.index.drop_duplicates(keep="last")]

    # merge nday_returns with signal
    nday_returns = returns.stack().rename("returns_0").to_frame()
    for i in range(1, n + 1):
        nday_returns["returns_{}".format(i)] = returns.shift(-i).stack()
    df_post_event_returns = signal.reset_index().merge(
        nday_returns.reset_index().rename(columns={"symbol": "assetid"})
    )
    return df_post_event_returns


if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(pathname)s} %(levelname)s: %(message)s",
    )

    try:
        df_signals_path = sys.argv[1]
    except IndexError:
        quit("Please provide a path to a signals file as the first argument.")
    try:
        event_drive_path = sys.argv[2]
        logging.info("File saved as: %s", event_drive_path)
    except IndexError:
        logging.info("Default path assumed to be current folder")
        event_drive_path = "./"

    df_signals = pd.read_csv(df_signals_path)

    if ".csv" not in df_signals_path:
        raise ValueError("Please provide a csv file.")
    if len(df_signals.columns.intersection(["signal", "date", "assetid"])) < 3:
        raise ValueError(
            "Please provide a csv file with columns: signal, date, assetid."
        )

    df_signals["date"] = pd.to_datetime(df_signals["date"])
    start = df_signals["date"].min()
    end = df_signals["date"].max()
    excess_returns = get_excess_returns(start, end, df_signals["assetid"])

    df_post_event_returns = post_event_returns(df_signals, excess_returns)
    df_post_event_returns.to_csv(event_drive_path + "event_driven_returns.csv")
