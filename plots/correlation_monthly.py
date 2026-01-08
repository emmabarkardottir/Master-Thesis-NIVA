import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

file1 = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx"
file2 = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixel_clean_correlation.xlsx"
output_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/correlation_plots"
os.makedirs(output_folder, exist_ok=True)

df1 = pd.read_excel(file1)
df2 = pd.read_excel(file2)
df2.columns = df2.columns.astype(str).str.strip()

df1 = df1[(df1['Nedre dyp'] >= 0) & (df1['Nedre dyp'] <= 5)]

parameter_name = "KLFA" # change here 
df1 = df1.rename(columns={
    parameter_name: "Parameter", 
    "Prøvetakingstidspunkt": "date", 
    "s": "Station"
})

sat_parameter = "chl_c2rcc"  # change here

# Verify that the sat_parameter column exists before assignment
if sat_parameter not in df2.columns:
    raise KeyError(f"Column '{sat_parameter}' not found in df2. Available columns: {list(df2.columns)}")

# Explicit assignment (NOT rename)
df2["Parameter"] = df2[sat_parameter]
df2["date"] = df2["pixel_time"]
df2["Station"] = df2["Name"]

# Convert date columns
df1['date'] = pd.to_datetime(df1['date'])
df2['date'] = pd.to_datetime(df2['date'])

stations = sorted(set(df1['Station']).intersection(set(df2['Station'])))

combined_df = []

for station in stations:

    df1_station = df1[df1['Station'] == station].copy()
    df2_station = df2[df2['Station'] == station].copy()

    df1_station['Year'] = pd.to_datetime(df1_station['date']).dt.year
    df1_station['Month'] = pd.to_datetime(df1_station['date']).dt.month

    df2_station['Year'] = pd.to_datetime(df2_station['date']).dt.year
    df2_station['Month'] = pd.to_datetime(df2_station['date']).dt.month

    # Monthly averages per year (drop NaN)
    df1_monthly = (
        df1_station.groupby(['Year', 'Month'])['Parameter']
        .mean()
        .dropna()
        .reset_index()
    )

    df2_monthly = (
        df2_station.groupby(['Year', 'Month'])['Parameter']
        .mean()
        .dropna()
        .reset_index()
    )

    # Keeps only months where BOTH datasets have data
    df_corr = pd.merge(
        df1_monthly,
        df2_monthly,
        on=['Year', 'Month'],
        how='inner',
        suffixes=('_in-situ', '_satellite')
    )

    if df_corr.empty:
        continue

    df_corr['Station'] = station
    combined_df.append(df_corr)

# Combine all stations
df_all = pd.concat(combined_df, ignore_index=True)

x = df_all['Parameter_in-situ'].values
y = df_all['Parameter_satellite'].values

corr, pval = pearsonr(x, y)
rmse = np.sqrt(np.mean((y - x)**2))
bias = np.mean(y - x)

# RMA regression
r = np.corrcoef(x, y)[0, 1]
slope_rma = np.sign(r) * (np.std(y, ddof=1) / np.std(x, ddof=1))
intercept_rma = np.mean(y) - slope_rma * np.mean(x)

print("Global statistics:")
print(f"  r = {corr:.3f}, RMSE = {rmse:.3f}, Bias = {bias:.3f}")
print(f"  RMA: y = {intercept_rma:.3f} + {slope_rma:.3f}x")

# plot combined
plt.figure(figsize=(7, 7))
colors = plt.cm.viridis(np.linspace(0, 1, len(stations)))

# Ensure VT12 is explicitly included in the plotting loop
for color, station in zip(colors, stations):
    df_station = df_all[df_all['Station'] == station]
    if df_station.empty:
        print(f"Skipping {station}: no data available.")
        continue

    plt.scatter(
        df_station['Parameter_in-situ'], 
        df_station['Parameter_satellite'], 
        alpha=0.7, 
        label=station,
        color=color,
        edgecolor='k',
        s=50
    )

    if station == 'VT12':
        print("VT12 data points plotted.")

# RMA regression line
min_val = min(np.min(x), np.min(y))
max_val = max(np.max(x), np.max(y))
x_line = np.linspace(min_val, max_val, 100)
y_rma = intercept_rma + slope_rma * x_line
plt.plot(x_line, y_rma, color='red', linewidth=2, label=f'RMA: y={intercept_rma:.2f}+{slope_rma:.2f}x')

plt.title(f'In-situ vs Satellite (Monthly Means)\n{parameter_name}\n'
          f'r={corr:.2f}, RMSE={rmse:.2f}, Bias={bias:.2f}')
plt.xlabel('In-situ (monthly mean)')
plt.ylabel('Satellite (monthly mean)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.grid(True)
plt.tight_layout()

# Save combined plot
save_path = os.path.join(output_folder, f"correlation_all_stations_{parameter_name}_c2rcc.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved combined correlation plot: {save_path}")

# Individual station plots
for station in stations:
    df_station = df_all[df_all['Station'] == station]
    if df_station.empty:
        continue

    x = df_station['Parameter_in-situ'].values
    y = df_station['Parameter_satellite'].values

    if len(x) < 2:
        print(f"Skipping {station}: not enough data points.")
        continue

    # Stats
    corr, pval = pearsonr(x, y)
    rmse = np.sqrt(np.mean((y - x) ** 2))
    bias = np.mean(y - x)

    r = np.corrcoef(x, y)[0, 1]
    slope_rma = np.sign(r) * (np.std(y, ddof=1) / np.std(x, ddof=1))
    intercept_rma = np.mean(y) - slope_rma * np.mean(x)

    plt.figure(figsize=(6, 6))
    plt.scatter(x, y, alpha=0.8, color='royalblue', edgecolor='k', s=60)

    # Regression line
    min_val = min(np.min(x), np.min(y))
    max_val = max(np.max(x), np.max(y))
    x_line = np.linspace(min_val, max_val, 100)
    y_rma = intercept_rma + slope_rma * x_line
    plt.plot(x_line, y_rma, color='red', linewidth=2, label=f'RMA: y={intercept_rma:.2f}+{slope_rma:.2f}x')

    plt.title(f'{station}\n{parameter_name}\n'
              f'r={corr:.2f}, RMSE={rmse:.2f}, Bias={bias:.2f}')
    plt.xlabel('In-situ (monthly mean)')
    plt.ylabel('Satellite (monthly mean)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    

    filename = f"monthly_correlation_{parameter_name}_c2rcc_{station.replace(' ', '_')}.png"
    save_path_station = os.path.join(output_folder, filename)
    plt.savefig(save_path_station, dpi=300, bbox_inches='tight')
    plt.close()

    plt.show()

    print(f"Saved plot for {station}: {save_path_station}")
