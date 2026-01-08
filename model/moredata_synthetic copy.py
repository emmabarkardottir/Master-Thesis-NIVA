import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge
from sklearn.neighbors import KernelDensity
import os

# -------------------------
# Configuration
# -------------------------
KLFA_METHOD = "lognormal"  # "lognormal" or "kde"
RNG_SEED = 42
n_synth = 200

# -------------------------
# Load & preprocess (adapt paths as needed)
# -------------------------
df_raw = pd.read_excel(
    "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx"
)
df_raw = df_raw[df_raw["s"] == "VT16"].copy()

df_raw = df_raw.rename(columns={
    "CDOM_insitu": "CDOM",
    "KLFA_insitu": "KLFA",
    "TSM_insitu": "TSM",
    "s": "Station",
    "Prøvetakingstidspunkt": "date"
})

df_raw["date"] = pd.to_datetime(df_raw["date"])

vars_to_model = ["KLFA", "TSM", "SECCI", "CDOM"]

# Identify fully-observed raw rows (as in your original script)
complete_raw = df_raw[df_raw[vars_to_model].notna().all(axis=1)].copy()
complete_raw_by_date = complete_raw.sort_values("date").drop_duplicates(subset="date", keep="first").set_index("date")
print("Number of unique dates in raw data with a fully observed row (should be 12):", len(complete_raw_by_date))

# Build daily aggregated table (same as yours)
df_daily = df_raw.groupby("date", as_index=False)[vars_to_model].mean()
df_daily["Station"] = "VT16"
df_daily["month"] = df_daily["date"].dt.month

df_daily_orig = df_daily.copy().set_index("date")

# -------------------------
# MICE imputation (same)
# -------------------------
imputer = IterativeImputer(
    estimator=BayesianRidge(),
    max_iter=50,
    random_state=RNG_SEED,
    sample_posterior=False,
)
imputed_all = imputer.fit_transform(df_daily[vars_to_model])

df_imp = df_daily.copy()
df_imp[vars_to_model] = imputed_all

# Restore exact original raw values for dates that had fully-observed raw rows
restored_dates = []
for d in df_imp["date"]:
    if d in complete_raw_by_date.index:
        orig_row = complete_raw_by_date.loc[d, vars_to_model]
        for v in vars_to_model:
            df_imp.loc[df_imp["date"] == d, v] = float(orig_row[v])
        restored_dates.append(d)

print("Restored exact raw rows for dates (count):", len(restored_dates))

# Mark imputed cells based on ORIGINAL daily dataframe (before any imputation)
for col in vars_to_model:
    df_imp[col + "_imputed"] = df_daily_orig[col].isna().astype(bool).values

if restored_dates:
    df_imp.loc[df_imp["date"].isin(restored_dates), [c + "_imputed" for c in vars_to_model]] = False

# Sanity check restored equality
mismatches = []
for d in restored_dates:
    imp_row = df_imp[df_imp["date"] == d].iloc[0]
    orig_row = complete_raw_by_date.loc[d]
    for v in vars_to_model:
        val_imp = float(imp_row[v])
        val_orig = float(orig_row[v])
        if not np.isclose(val_imp, val_orig, atol=0.0):
            mismatches.append((d, v, val_orig, val_imp))

if mismatches:
    print("ERROR: mismatches found between restored and original raw rows:")
    for m in mismatches:
        print(m)
    raise AssertionError("Restored rows do not exactly match original raw rows. See above.")
else:
    print("All restored rows match the corresponding raw data rows exactly.")

# -------------------------
# Physical bounds (same)
# -------------------------
bounds = {
    "SECCI": (5, 25),
    "CDOM": (0.07, 0.56),
    "KLFA": (0.12, 5.1),
    "TSM": (0.097, 5.9)
}
for col, (lower, upper) in bounds.items():
    df_imp[col] = df_imp[col].clip(lower, upper)

# -------------------------
# Prepare to generate synthetic rows (keeps your monthly MVN sampling)
# -------------------------
rng = np.random.default_rng(RNG_SEED)
vars_ = vars_to_model
df_full = df_imp.copy()

global_mean = df_full[vars_].mean().values
global_cov  = df_full[vars_].cov().values

month_stats = {}
for m in range(1, 13):
    dfm = df_full[df_full["month"] == m][vars_]
    if len(dfm) >= 4:
        mean_m = dfm.mean().values
        cov_m  = dfm.cov().values
        n = len(dfm)
        alpha = min(1.0, n / 20)
        mean_used = alpha * mean_m + (1 - alpha) * global_mean
        cov_used  = alpha * cov_m  + (1 - alpha) * global_cov
    else:
        mean_used = global_mean
        cov_used  = global_cov
    month_stats[m] = (mean_used, cov_used)

counts_by_month = df_full["month"].value_counts().reindex(range(1, 13), fill_value=0).values
inv = (counts_by_month.max() + 1) - counts_by_month
if inv.sum() == 0:
    per_month_alloc = np.full(12, n_synth // 12)
else:
    per_month_alloc = np.floor(n_synth * inv / inv.sum()).astype(int)
rem = n_synth - per_month_alloc.sum()
for i in range(rem):
    per_month_alloc[i % 12] += 1

# -------------------------
# Pre-fit global KLFA distributions (for fallback) and per-month if enough data
# -------------------------
# We'll compute per-month parameters for lognormal and per-month KDE for KDE method.
klfa_month_params = {}
klfa_global_vals = df_full["KLFA"][df_full["KLFA"] > 0].values  # positive values for KLFA
if len(klfa_global_vals) < 5:
    raise RuntimeError("Not enough positive KLFA values to fit global distribution.")

# global lognormal fit (fit normal on log-values)
log_glob = np.log(klfa_global_vals)
glob_mu, glob_sigma = log_glob.mean(), log_glob.std()

# global KDE fit (fit on positive KLFA)
kde_global = KernelDensity(kernel="gaussian", bandwidth=0.15).fit(klfa_global_vals.reshape(-1, 1))

for m in range(1, 13):
    vals_m = df_full[df_full["month"] == m]["KLFA"]
    vals_m_pos = vals_m[vals_m > 0].values
    if len(vals_m_pos) >= 5:
        # lognormal params
        mu_m = np.log(vals_m_pos).mean()
        sigma_m = np.log(vals_m_pos).std()
        # KDE
        kde_m = KernelDensity(kernel="gaussian", bandwidth=0.15).fit(vals_m_pos.reshape(-1, 1))
        klfa_month_params[m] = {"mu": mu_m, "sigma": sigma_m, "kde": kde_m}
    else:
        # fallback to global
        klfa_month_params[m] = {"mu": glob_mu, "sigma": glob_sigma, "kde": kde_global}

# -------------------------
# Generate synthetic multivariate draws per month AND replace KLFA using chosen method
# -------------------------
synth_rows = []
for month_idx, k in enumerate(per_month_alloc, start=1):
    mean_used, cov_used = month_stats[month_idx]
    cov_reg = cov_used
    if k <= 0:
        continue

    # 1) generate MVN draws (same as before)
    draws = rng.multivariate_normal(mean=mean_used, cov=cov_reg, size=k)

    # 2) create dates for synthetic rows (same as before)
    years = rng.integers(2018, 2024, size=k)
    days = []
    for y in years:
        last = pd.Timestamp(year=y, month=month_idx, day=1) + pd.offsets.MonthEnd(0)
        d = rng.integers(1, last.day + 1)
        days.append(pd.Timestamp(year=y, month=month_idx, day=int(d)))

    # 3) generate KLFA samples for this month using chosen method
    params = klfa_month_params[month_idx]
    if KLFA_METHOD == "lognormal":
        # sample in log-space then exp
        klfa_samples = np.exp(rng.normal(loc=params["mu"], scale=params["sigma"], size=k))
    elif KLFA_METHOD == "kde":
        # use the per-month KDE to sample
        klfa_samples = params["kde"].sample(k).reshape(-1)
        # KDE.sample may produce tiny negative numerical artifacts -> clip to positive
        klfa_samples = np.maximum(klfa_samples, 1e-8)
    else:
        raise ValueError("KLFA_METHOD must be 'lognormal' or 'kde'")

    # clip KLFA samples to physical bounds BEFORE mapping:
    klfa_samples = np.clip(klfa_samples, bounds["KLFA"][0], bounds["KLFA"][1])

    # 4) Map new KLFA samples into draws using rank (quantile) mapping to preserve rank-relationships:
    #    - compute ranks of original KLFA values in draws
    #    - assign KLFA samples sorted to the draws according to ranks
    col_idx = vars_.index("KLFA")
    original_klfa_draws = draws[:, col_idx]

    # get order (argsort) of original draws
    order_original = np.argsort(original_klfa_draws)
    # get order of synthesized samples (sorted)
    order_samples = np.argsort(klfa_samples)

    # create a copy to replace KLFA column
    new_klfa_for_draws = original_klfa_draws.copy()
    # assign samples so that smallest original draw gets smallest sample, etc.
    new_klfa_for_draws[order_original] = klfa_samples[order_samples]

    # replace KLFA column in draws
    draws[:, col_idx] = new_klfa_for_draws

    # 5) assemble rows
    for row_vals, d in zip(draws, days):
        row = {"date": d}
        for j, col in enumerate(vars_):
            row[col] = float(row_vals[j])
        row["Station"] = "VT16"
        row["is_interpolated"] = True
        synth_rows.append(row)

# Build synthetic DataFrame
df_synth = pd.DataFrame(synth_rows)

# Apply bounds to synthetic too (safety)
for col, (lower, upper) in bounds.items():
    if col in df_synth.columns:
        df_synth[col] = df_synth[col].clip(lower, upper)

# Set 'is_interpolated' for df_full as you had
df_full["is_interpolated"] = df_full[[v + "_imputed" for v in vars_]].any(axis=1)

# Combine and save
combined = pd.concat([
    df_full[["date", "Station"] + vars_ + ["is_interpolated"]],
    df_synth[["date", "Station"] + vars_ + ["is_interpolated"]]
], ignore_index=True)

output_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/model/VT16_imputed_plus_syntheticTEST.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
combined.to_csv(output_path, index=False)

print("DONE!")
print("Real rows:", len(df_full), "   Synthetic rows:", len(df_synth))
print("Total:", len(combined))
print("KLFA method used:", KLFA_METHOD)
