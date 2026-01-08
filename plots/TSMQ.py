import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Load data
df_discharge = pd.read_csv("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/NVE_data/discharge/Q_daily-mean_ Flåm bru_ Flåm bru_72.77.0_download-2025-09-24.csv")
df_tsm = pd.read_excel("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixel_clean.xlsx")

df_discharge = df_discharge.dropna(subset=["value"])
# choose station VT79 
df_tsm = df_tsm[df_tsm["Name"] == "VT79"].copy()
df_tsm = df_tsm.dropna(subset=["spm_nechad_665_mean"])
df_tsm = df_tsm.rename(columns={"spm_nechad_665_mean": "TSM"})

# percentile
lower_percentile = 0
upper_percentile = 99

low_thresh = np.percentile(df_tsm["TSM"], lower_percentile)
high_thresh = np.percentile(df_tsm["TSM"], upper_percentile)

df_tsm = df_tsm[(df_tsm["TSM"] >= low_thresh) & (df_tsm["TSM"] <= high_thresh)].copy()

df_discharge["date"] = pd.to_datetime(df_discharge["datetime"]).dt.tz_localize(None)
df_tsm["pixel_time"] = pd.to_datetime(df_tsm["pixel_time"]).dt.tz_localize(None)

df_discharge = df_discharge.sort_values("date")
df_tsm = df_tsm.sort_values("pixel_time")

years = range(2018, 2024)
param_name = "TSM_665"
riv_name = "Flåm bru"
station = "72.77.0"

fig, axes = plt.subplots(3, 2, figsize=(14, 12), sharex=False)
axes = axes.flatten()

for i, year in enumerate(years):
    ax1 = axes[i]

    start_date = pd.to_datetime(f"{year}-01-01")
    end_date = pd.to_datetime(f"{year}-12-31")

    # Filter data for current year
    d_dis = df_discharge[(df_discharge["date"] >= start_date) & (df_discharge["date"] <= end_date)]
    d_tsm = df_tsm[(df_tsm["pixel_time"] >= start_date) & (df_tsm["pixel_time"] <= end_date)]

    # Left axis: river discharge
    ax1.plot(d_dis["date"], d_dis["value"], label="Discharge [m³/s]", color="blue")
    ax1.set_ylabel("Discharge [m³/s]", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Right axis: TSM
    ax2 = ax1.twinx()
    ax2.plot(d_tsm["pixel_time"], d_tsm["TSM"], label="TSM (g/m$^{3}$)", color="teal")
    ax2.set_ylabel(f"{param_name} [g/m$^{3}$]", color="teal")
    ax2.tick_params(axis="y", labelcolor="teal")

    ax1.set_title(f"Year {year}")
    ax1.grid(True, linestyle="--", alpha=0.5)

fig.suptitle(f"Comparison of River Discharge at {riv_name} ({station}) and Satellite TSM Concentration (2018–2023)", fontsize=16, fontweight="bold")

# Save plot
plt.tight_layout()
plot_output = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/QC_plots"
filename = f"{riv_name}_{param_name}.png"
plt.savefig(os.path.join(plot_output, filename), dpi=300)
plt.show()