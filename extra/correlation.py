import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

file1 = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx"
file2 = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixel_clean.xlsx"
output_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/correlation_plots"
os.makedirs(output_folder, exist_ok=True)

df1 = pd.read_excel(file1)
df2 = pd.read_excel(file2)

df1 = df1[df1['Nedre dyp'] == 0]  # only surface data for in-situ

df1 = df1.rename(columns={
    "KLFA": "Parameter", # Change this to the desired parameter column
    "Prøvetakingstidspunkt": "date", 
    "s": "Station"
})
df2 = df2.rename(columns={
    "chl_c2rcc_mean": "Parameter",  # Change this to the desired parameter column
    "pixel_time": "date", 
    "Name": "Station"
})

parameter_name = "KLFA" # Change this to the desired parameter

df1['date'] = pd.to_datetime(df1['date']).dt.date
df2['date'] = pd.to_datetime(df2['date']).dt.date

stations = sorted(set(df1['Station']).intersection(set(df2['Station'])))

combined_df = []

for station in stations:
    df1_station = df1[df1['Station'] == station]
    df2_station = df2[df2['Station'] == station]

    df_corr = pd.merge(
        df1_station[['date', 'Parameter']], 
        df2_station[['date', 'Parameter']], 
        on='date', 
        suffixes=('_in-situ', '_satellite')
    )

    # Clean data
    df_corr = df_corr.replace([np.inf, -np.inf], np.nan).dropna()
    if df_corr.empty:
        continue

    df_corr['Station'] = station
    combined_df.append(df_corr)

if not combined_df:
    raise ValueError("No overlapping data found for any stations.")

df_all = pd.concat(combined_df, ignore_index=True)

# Statisitcs
x = df_all['Parameter_in-situ'].values
y = df_all['Parameter_satellite'].values

corr, pval = pearsonr(x, y)
rmse = np.sqrt(np.mean((y - x)**2))
bias = np.mean(y - x)

r = np.corrcoef(x, y)[0, 1]
slope_rma = np.sign(r) * (np.std(y, ddof=1) / np.std(x, ddof=1))
intercept_rma = np.mean(y) - slope_rma * np.mean(x)

print("\nGlobal statistics:")
print(f"  r = {corr:.3f}, RMSE = {rmse:.3f}, Bias = {bias:.3f}")
print(f"  RMA: y = {intercept_rma:.3f} + {slope_rma:.3f}x")

# combined station plot
plt.figure(figsize=(7, 7))
colors = plt.cm.viridis(np.linspace(0, 1, len(stations)))

for color, station in zip(colors, stations):
    df_station = df_all[df_all['Station'] == station]
    plt.scatter(
        df_station['Parameter_in-situ'], 
        df_station['Parameter_satellite'], 
        alpha=0.7, 
        label=station,
        color=color,
        edgecolor='k',
        s=50
    )

# RMA regression line
min_val = min(np.min(x), np.min(y))
max_val = max(np.max(x), np.max(y))
x_line = np.linspace(min_val, max_val, 100)
y_rma = intercept_rma + slope_rma * x_line
plt.plot(x_line, y_rma, color='red', linewidth=2, label=f'RMA: y={intercept_rma:.2f}+{slope_rma:.2f}x')

plt.title(f'In-situ vs Satellite (All Stations)\n'f'r={corr:.2f}, RMSE={rmse:.2f}, Bias={bias:.2f}')
plt.xlabel('In-situ measurement')
plt.ylabel('Satellite measurement - conc_chl_mean')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.grid(True)
plt.tight_layout()

# Save figure
# save_path = os.path.join(output_folder, f"correlation_all_stations_{parameter_name}.png")
# plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.show()

# Individual station plots
for station in stations:
    df_station = df_all[df_all['Station'] == station]
    if df_station.empty:
        continue

    x = df_station['Parameter_in-situ'].values
    y = df_station['Parameter_satellite'].values

    # Statistics
    corr, pval = pearsonr(x, y)
    rmse = np.sqrt(np.mean((y - x) ** 2))
    bias = np.mean(y - x)

    # RMA regression
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

    plt.title(f'{station}\nr={corr:.2f}, RMSE={rmse:.2f}, Bias={bias:.2f}')
    plt.xlabel('In-situ measurement')
    plt.ylabel('Satellite measurement - conc_chl_mean')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Save individual figure
    # filename = f"correlation_{parameter_name}_{station.replace(' ', '_')}.png"
    # save_path_station = os.path.join(output_folder, filename)
    # plt.savefig(save_path_station, dpi=300, bbox_inches='tight')
    plt.show()
