import pandas as pd
import matplotlib.pyplot as plt

insitu_real = pd.read_excel("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx")
insitu_real = insitu_real.rename(columns={ "Prøvetakingstidspunkt": "date", "s": "Station", "CDOM": "CDOM_insitu", "KLFA": "KLFA_insitu", "TSM": "TSM_insitu", "SECCI": "SECCI_insitu"})
insitu_synthetic = pd.read_csv("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/model/VT16_imputed_plus_syntheticTEST.csv") 
insitu_synthetic = insitu_synthetic.rename(columns= {"CDOM": "CDOM_insitu", "KLFA": "KLFA_insitu", "TSM": "TSM_insitu", "SECCI": "SECCI_insitu"})

# Choose station
choice = 1
station_dict = {1: "VT16", 2: "VT79", 3: ["VT16", "VT79"]}
chosen_station = station_dict[choice]

# Filter both datasets
insitu_real = insitu_real[insitu_real["Station"] == chosen_station]
insitu_synthetic = insitu_synthetic[insitu_synthetic["Station"] == chosen_station]

# Parse dates and set index
for df in [insitu_real, insitu_synthetic]:
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values("date", inplace=True)
    df.set_index("date", inplace=True)

# Extract variables
CDOM_real = insitu_real["CDOM_insitu"]
CHL_real  = insitu_real["KLFA_insitu"]
TSM_real  = insitu_real["TSM_insitu"]
SECCI_real = insitu_real["SECCI_insitu"]

CDOM_syn = insitu_synthetic["CDOM_insitu"]
CHL_syn  = insitu_synthetic["KLFA_insitu"]
TSM_syn  = insitu_synthetic["TSM_insitu"]
SECCI_syn = insitu_synthetic["SECCI_insitu"]

# ---------- Histograms ----------
fig, axes = plt.subplots(2, 2, figsize=(16, 8))
fig.suptitle("Real vs Synthetic Data Distributions", fontsize=15)

# CDOM
axes[0, 0].hist(CDOM_real, bins=20, alpha=0.6, label="Real", edgecolor="black")
axes[0, 0].hist(CDOM_syn,  bins=20, alpha=0.6, label="Synthetic", edgecolor="black")
axes[0, 0].set_title("CDOM")
axes[0, 0].set_xlabel("CDOM (m⁻¹)")
axes[0, 0].set_ylabel("Count")
axes[0, 0].legend()
axes[0, 0].grid(True, linestyle="--", alpha=0.3)

# KLFA
axes[0, 1].hist(CHL_real, bins=20, alpha=0.6, label="Real", edgecolor="black")
axes[0, 1].hist(CHL_syn,  bins=20, alpha=0.6, label="Synthetic", edgecolor="black")
axes[0, 1].set_title("KLFA")
axes[0, 1].set_xlabel("CHL-a (mg m$^{-3}$)")
axes[0, 1].legend()
axes[0, 1].grid(True, linestyle="--", alpha=0.3)

# TSM
axes[1, 0].hist(TSM_real, bins=20, alpha=0.6, label="Real", edgecolor="black")
axes[1, 0].hist(TSM_syn,  bins=20, alpha=0.6, label="Synthetic", edgecolor="black")
axes[1, 0].set_title("TSM")
axes[1, 0].set_xlabel("TSM (g m$^{-3}$)")
axes[1, 0].set_ylabel("Count")
axes[1, 0].legend()
axes[1, 0].grid(True, linestyle="--", alpha=0.3)

# SECCI
axes[1, 1].hist(SECCI_real, bins=20, alpha=0.6, label="Real", edgecolor="black")
axes[1, 1].hist(SECCI_syn,  bins=20, alpha=0.6, label="Synthetic", edgecolor="black")
axes[1, 1].set_title("SECCI")
axes[1, 1].set_xlabel("SECCI (m⁻¹)")
axes[1, 1].legend()
axes[1, 1].grid(True, linestyle="--", alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.95])
# save plot
plt.savefig("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/model/histogram_comparison.png")
plt.show()

# ---------- Time Series ----------
fig, axes = plt.subplots(2, 2, figsize=(16, 8))
fig.suptitle("Real vs Synthetic Data Time Series", fontsize=15)

# CDOM
axes[0, 0].plot(CDOM_real.index, CDOM_real, marker='o', label="Real")
axes[0, 0].plot(CDOM_syn.index, CDOM_syn, marker='x', label="Synthetic")
axes[0, 0].set_title("CDOM")
axes[0, 0].set_ylabel("CDOM (m⁻¹)")
axes[0, 0].legend()
axes[0, 0].grid(True, linestyle="--", alpha=0.3)

# KLFA
axes[0, 1].plot(CHL_real.index, CHL_real, marker='o', label="Real")
axes[0, 1].plot(CHL_syn.index, CHL_syn, marker='x', label="Synthetic")
axes[0, 1].set_title("KLFA")
axes[0, 1].set_ylabel("CHL-a (mg m$^{-3}$)")
axes[0, 1].legend()
axes[0, 1].grid(True, linestyle="--", alpha=0.3)

# TSM
axes[1, 0].plot(TSM_real.index, TSM_real, marker='o', label="Real")
axes[1, 0].plot(TSM_syn.index, TSM_syn, marker='x', label="Synthetic")
axes[1, 0].set_title("TSM")
axes[1, 0].set_ylabel("TSM (g m$^{-3}$)")
axes[1, 0].legend()
axes[1, 0].grid(True, linestyle="--", alpha=0.3)

# SECCI
axes[1, 1].plot(SECCI_real.index, SECCI_real, marker='o', label="Real")
axes[1, 1].plot(SECCI_syn.index, SECCI_syn, marker='x', label="Synthetic")
axes[1, 1].set_title("SECCI")
axes[1, 1].set_ylabel("SECCI (m⁻¹)")
axes[1, 1].legend()
axes[1, 1].grid(True, linestyle="--", alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.95])

# save plot
plt.savefig("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/model/time_series_comparison.png")
plt.show()
