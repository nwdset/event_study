# %%
import pandas as pd

from statsmodels.regression.rolling import RollingOLS


# %%
assetid = pd.read_pickle("/home/jeff/LR-Research/event_study/assetid_returns.pickle")
spy = pd.read_pickle("/home/jeff/LR-Research/event_study/spy_returns.pickle").rename(
    "spy"
)
assetid = assetid.add_prefix("assetid_")


# %%
col = assetid.columns[50]


# %%
betas = []
for col in assetid:
    beta = (
        RollingOLS.from_formula(
            f"{col} ~ spy + 1",
            pd.concat([assetid[col], spy], axis=1).dropna(),
            window=60,
        )
        .fit()
        .params["spy"]
        .rename(int(col.replace("assetid_", "")))
        .reindex(assetid.index)
        .fillna(0)
    )
    betas.append(beta)

# %%
betas = pd.concat(betas, axis=1)
betas = betas.replace({0: 1})

# %%
betas

# %%

# %%

# %%
