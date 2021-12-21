import numpy as np
import pandas as pd

import matplotlib.pyplot as plt


def event_driven_plot(event_returns: pd.DataFrame, event=None) -> plt.Axes:
    if not set(["date", "assetid", "signal"]) <= set(event_returns.columns):
        raise ValueError(
            "Event returns dataframe must have columns: date, assetid, signal, fdasfsd"
        )

    if event not in event_returns.colums:
        raise KeyError("Selected signal doesn't exist")

    event_returns = event_returns.set_index(["date", "assetid", "signal"]).cumsum(
        axis=1
    )

    fig, ax = plt.subplots(3, 1, figsize=(16, 16))
    event_returns.query(f"signal == {event}").boxplot(ax=ax[0])
    event_returns.query(f"signal == {event}").mean().plot(ax=ax[1])
    event_returns.query(f"signal == {event}").pipe(
        lambda x: np.mean(x) / np.std(x) * np.sqrt(len(x))
    ).plot(ax=ax[2])

    ax[0].set_title(f"Return Distribution Over Holding Horizon (signal={event})")
    ax[1].set_title("Cumulative Return Over Holding Horizon")
    ax[2].set_title("Return T-Statistic Over Holding Horizon")
    fig.set_facecolor("white")
    return fig


if __name__ == "__main__":
    event_drive_returns = pd.read_csv("./event_driven_returns.csv", index_col=0)
    figure = event_driven_plot(event_drive_returns, event=1)
    plt.show()
