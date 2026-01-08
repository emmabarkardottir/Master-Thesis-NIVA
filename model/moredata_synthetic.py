import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge
import os

# --- load & filter (same as your original script) ---
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

# variables
vars_to_model = ["KLFA", "TSM", "SECCI", "CDOM"]

# --- identify raw rows that are fully observed (the "true" 12) ---
complete_raw = df_raw[df_raw[vars_to_model].notna().all(axis=1)].copy()
# Deduplicate by date just in case there are multiple fully-observed rows per date:
# we'll keep the first occurrence for that date (you can change logic if you prefer).
complete_raw_by_date = complete_raw.sort_values("date").drop_duplicates(subset="date", keep="first").set_index("date")

print("Number of unique dates in raw data with a fully observed row (should be 12):", len(complete_raw_by_date))

# --- build daily aggregated dataframe (as you did) ---
df_daily = df_raw.groupby("date", as_index=False)[vars_to_model].mean()
df_daily["Station"] = "VT16"
df_daily["month"] = df_daily["date"].dt.month

# Save a copy for diagnostics & restoration
df_daily_orig = df_daily.copy().set_index("date")

# --- Run MICE on the daily table but DO NOT rely on its output for dates we have a fully-observed raw row ---
imputer = IterativeImputer(
    estimator=BayesianRidge(),
    max_iter=50,
    random_state=42,
    sample_posterior=False
)

# Fit/transform on the daily table (will give values for every row)
imputed_all = imputer.fit_transform(df_daily[vars_to_model])

df_imp = df_daily.copy()
df_imp[vars_to_model] = imputed_all

# --- Now restore exact original raw values for any date where raw had a fully-observed row ---
# For each date in df_imp that exists in complete_raw_by_date.index, overwrite vars with that raw row's exact values.
restored_dates = []
for d in df_imp["date"]:
    if d in complete_raw_by_date.index:
        orig_row = complete_raw_by_date.loc[d, vars_to_model]
        # Ensure we have the exact values and types (float)
        for v in vars_to_model:
            df_imp.loc[df_imp["date"] == d, v] = float(orig_row[v])
        restored_dates.append(d)

print("Restored exact raw rows for dates (count):", len(restored_dates))

# --- Mark imputed cells based on ORIGINAL daily dataframe (before any imputation) ---
# A value is considered imputed if it was NaN in the aggregated daily table (df_daily_orig)
for col in vars_to_model:
    df_imp[col + "_imputed"] = df_daily_orig[col].isna().astype(bool).values

# Also, for any restored date (that came from a fully-observed raw row) ensure imputed flags are FALSE
if restored_dates:
    df_imp.loc[df_imp["date"].isin(restored_dates), [c + "_imputed" for c in vars_to_model]] = False

# --- Sanity checks: Ensure restored rows exactly match the original raw rows we used for restoration ---
mismatches = []
for d in restored_dates:
    # compare df_imp row (post restore) to complete_raw_by_date row
    imp_row = df_imp[df_imp["date"] == d].iloc[0]
    orig_row = complete_raw_by_date.loc[d]
    for v in vars_to_model:
        val_imp = float(imp_row[v])
        val_orig = float(orig_row[v])
        if not np.isclose(val_imp, val_orig, atol=0.0):  # exact equality if both floats serialized same
            mismatches.append((d, v, val_orig, val_imp))

if mismatches:
    # show mismatches for debugging and stop
    print("ERROR: mismatches found between restored and original raw rows:")
    for m in mismatches:
        print(m)
    raise AssertionError("Restored rows do not exactly match original raw rows. See above.")
else:
    print("All restored rows match the corresponding raw data rows exactly.")

# --- Apply physical bounds to the imputed/restored dataframe (same bounds you used) ---
bounds = {
    "SECCI": (5, 25),
    "CDOM": (0.07, 0.56),
    "KLFA": (0.12, 5.1),
    "TSM": (0.097, 5.9)
}
for col, (lower, upper) in bounds.items():
    df_imp[col] = df_imp[col].clip(lower, upper)

# --- Generate synthetic data exactly as before (unchanged) ---
n_synth = 200
rng = np.random.default_rng(42)
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

synth_rows = []
for month_idx, k in enumerate(per_month_alloc, start=1):
    mean_used, cov_used = month_stats[month_idx]
    jitter = 1e-8 * np.eye(cov_used.shape[0])
    cov_reg = cov_used + jitter
    if k <= 0:
        continue
    draws = rng.multivariate_normal(mean=mean_used, cov=cov_reg, size=k)
    years = rng.integers(2018, 2024, size=k)
    days = []
    for y in years:
        last = pd.Timestamp(year=y, month=month_idx, day=1) + pd.offsets.MonthEnd(0)
        d = rng.integers(1, last.day + 1)
        days.append(pd.Timestamp(year=y, month=month_idx, day=int(d)))
    for row_vals, d in zip(draws, days):
        row = {"date": d}
        for j, col in enumerate(vars_):
            row[col] = float(row_vals[j])
        row["Station"] = "VT16"
        row["is_interpolated"] = True
        synth_rows.append(row)

df_synth = pd.DataFrame(synth_rows)
for col, (lower, upper) in bounds.items():
    df_synth[col] = df_synth[col].clip(lower, upper)

df_full["is_interpolated"] = df_full[[v + "_imputed" for v in vars_]].any(axis=1)

combined = pd.concat([
    df_full[["date", "Station"] + vars_ + ["is_interpolated"]],
    df_synth[["date", "Station"] + vars_ + ["is_interpolated"]]
], ignore_index=True)

# --- Save results ---
output_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/model/VT16_imputed_plus_synthetic.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
combined.to_csv(output_path, index=False)

print("DONE!")
print("Real rows:", len(df_full), "   Synthetic rows:", len(df_synth))
print("Total:", len(combined))
