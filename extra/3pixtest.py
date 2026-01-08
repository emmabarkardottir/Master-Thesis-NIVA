import pandas as pd

# === 1. Load data ===
df = pd.read_excel("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixelextractions_raw.xlsx") 

# === 2. Define your parameter columns ===
param_cols = [
    "rtoa_4","rtoa_6","rtoa_8","rtoa_17",
    "rhow_1","rhow_2","rhow_3","rhow_4","rhow_5","rhow_6","rhow_7","rhow_8",
    "rhow_9","rhow_10","rhow_11","rhow_12","rhow_16","rhow_17","rhow_18","rhow_21",
    "iop_apig","iop_adet","iop_agelb","iop_bpart","iop_bwit",
    "iop_adg","iop_atot","iop_btot","kd489","kd_z90max",
    "conc_tsm","conc_chl",
    "spm_nechad_665","spm_nechad_865","tur_nechad_665","tur_nechad_865",
    "chl_oc4","c2rcc_secchi_depth_1","c2rcc_secchi_depth_2",
    "c2rcc_secchi_depth_3","c2rcc_secchi_depth_4",
    "chl_c2rcc","chl_merged_pitarch10_50","chl_merged_pitarch15_50",
    "chl_merged_pci_pitarch10_50","chl_merged_pci_pitarch15_50",
    "chl_calib_c2rcc","chl"
]

# Keep only columns that exist
param_cols = [c for c in param_cols if c in df.columns]

# === 3. Group and aggregate ===
group_cols = ["CALVALUS_ID", "ID_full", "Name",	"Lat", "Lon", "ID",	"source_name", "pixel_time"]

# Define aggregation rules
agg_dict = {
    "pixel_lat": "mean",
    "pixel_lon": "mean"
}

# Add mean and std for all scientific parameters
for col in param_cols:
    agg_dict[col] = ["mean", "std"]

# Perform the aggregation
aggregated = df.groupby(group_cols, as_index=False).agg(agg_dict)

# Add pixel count (number of pixels in each group)
aggregated["n_pixels"] = df.groupby(group_cols).size().values

# Flatten multi-level columns from aggregation
aggregated.columns = [
    "_".join(col).rstrip("_") if isinstance(col, tuple) else col
    for col in aggregated.columns
]

# === 4. Save results ===
aggregated.to_excel(
    "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixel_clean.xlsx",
    index=False
)

print(f"Saved aggregated 3×3 box stats with n_pixels ({len(param_cols)} parameters, mean/std for each).")
