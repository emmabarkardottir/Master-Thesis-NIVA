import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import numpy as np

# Load data
df_discharge = pd.read_csv("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/NVE_data/discharge/Q_daily-mean_ Stuvane_ Stuvane_73.2.0_download-2025-09-24.csv")
df_C = pd.read_excel("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/RS_Lærdalselva.xlsx")

# Drop rows with NaN values
df_discharge = df_discharge.dropna(subset=["value"])
df_C = df_C.dropna(subset=["TSM"])

# Rename columns
df_C = df_C.rename(columns={"TSM": "Concentration"})

# Remove "<" from Concentration values
df_C["Concentration"] = df_C["Concentration"].str.replace("<", "", regex=False)

# Convert Concentration to numeric
df_C["Concentration"] = df_C["Concentration"].str.replace(",", ".", regex=False) 
df_C["Concentration"] = pd.to_numeric(df_C["Concentration"], errors="coerce")

# Convert datetime columns and create a 'date' column
df_discharge["date"] = pd.to_datetime(df_discharge["datetime"]).dt.date
df_C["date"] = pd.to_datetime(df_C["Sample date"]).dt.date

# Filter to include only matching dates
matching_dates = set(df_discharge["date"]).intersection(df_C["date"])
df_discharge = df_discharge[df_discharge["date"].isin(matching_dates)]
df_C = df_C[df_C["date"].isin(matching_dates)]

df_discharge = df_discharge.sort_values(by="date")
df_C = df_C.sort_values(by="date")

merged_df = pd.merge(df_discharge, df_C, on="date", how="inner")

# Ensure numeric
merged_df["value"] = pd.to_numeric(merged_df["value"], errors="coerce")
merged_df["Concentration"] = pd.to_numeric(merged_df["Concentration"], errors="coerce")

# DROP all rows where either value or concentration is missing
merged_df = merged_df.dropna(subset=["value", "Concentration"])

# Extract arrays
x = merged_df["value"].values
y = merged_df["Concentration"].values

# Calculate stats
corr, pval = pearsonr(x, y)
rmse = np.sqrt(np.mean((y - x)**2))
bias = np.mean(y - x)

r = np.corrcoef(x, y)[0, 1]
slope_rma = np.sign(r) * (np.std(y, ddof=1) / np.std(x, ddof=1))
intercept_rma = np.mean(y) - slope_rma * np.mean(x)

print("r:", corr)
print("RMSE:", rmse)
print("Bias:", bias)
print("RMA:", slope_rma, intercept_rma)

# -----------------------------
# Plot
# -----------------------------

plt.figure(figsize=(8, 6))

# Data points
plt.scatter(
    x, y,
    alpha=0.7,
    edgecolor='k',
    color='blue',
    s=60,
    label='Data points'
)

# RMA regression line
x_line = np.linspace(np.min(x), np.max(x), 500)
y_line = intercept_rma + slope_rma * x_line

plt.plot(
    x_line,
    y_line,
    linewidth=2,
    color='red',
    label=f"RMA: y = {intercept_rma:.2f} + {slope_rma:.2f}x\n(r = {corr:.2f})"
)

plt.xlabel("Discharge")
plt.ylabel("Concentration")
plt.title("Concentration vs. Discharge (RMA Regression)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()