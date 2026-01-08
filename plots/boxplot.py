import pandas as pd
import matplotlib.pyplot as plt
import os

choice = 2
station = {
     1: "VT12", 
     2: "VT16", 
     3: "VT79"
}
station_name = station[choice]

file_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx"
output_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/box_plots/used"
os.makedirs(output_folder, exist_ok=True)

df = pd.read_excel(file_path)

df = df[(df['Nedre dyp'] >= 0) & (df['Nedre dyp'] <= 5)]

time_col = "Prøvetakingstidspunkt"
df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

df_station = df[df["s"] == station_name].copy().dropna(subset=[time_col])
df_station["Year"] = df_station[time_col].dt.year
df_station["Month"] = df_station[time_col].dt.month

params = ["CDOM", "TSM", "TURB", "KLFA", "SECCI"]

# Units for y-axis
param_units = {
    "CDOM": r"m$^{-1}$",
    "TSM": r"g m$^{-3}$",
    "TURB": "FNU",
    "KLFA": r"mg m$^{-3}$",
    "SECCI": "m"
}

def trim_to_99th_percentile(series):
    if len(series) == 0:
        return series
    p99 = series.quantile(0.99)
    return series[series <= p99]

# MONTHLY DISTRIBUTIONS ACROSS ALL YEARS
fig, axes = plt.subplots(len(params), 1, figsize=(12, 3 * len(params)), sharex=True)

for i, param in enumerate(params):
    ax = axes[i]
    
    param_data_all_years = []
    for m in range(1, 13):
        # Skip January for TURB at VT79
        if param == "TURB" and m == 1:
            param_data_all_years.append([])
            continue
        
        monthly_data = df_station[df_station["Month"] == m][param].dropna()
        param_data_all_years.append(
            monthly_data.values if len(monthly_data) > 0 else []
        )

    ax.boxplot(
        param_data_all_years,
        positions=range(1, 13),
        widths=0.6,
        patch_artist=True,
        boxprops=dict(facecolor='lightgreen', alpha=0.5),
        medianprops=dict(color='red')
    )
    
    ax.set_ylabel(f"{param} ({param_units.get(param, '')})")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title(f"{param} – monthly distribution (all years)")

axes[-1].set_xticks(range(1, 13))
axes[-1].set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
axes[-1].set_xlabel("Month")

fig.suptitle(
    f"Seasonal variability of surface water properties at station {station_name},\n 99th percentile trimmed data \n"
    "(in-situ measurements, 0–5 m, all years)",
    fontsize=14
)

plt.tight_layout(rect=[0, 0, 1, 0.95])

filename_all = f"{station_name}_AllYears99.png"
plt.savefig(os.path.join(output_folder, filename_all), dpi=300)
plt.show()
plt.close(fig)
