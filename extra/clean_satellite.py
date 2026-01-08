import pandas as pd
import re

# === 1. Load original data ===
df = pd.read_excel(
    "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixelextractions_raw.xlsx"
)

# === 2. Check and remove duplicates (excluding CALVALUS_ID) ===
df_no_id = df.drop(columns=["CALVALUS_ID"])
num_duplicates = df_no_id.duplicated().sum()
print(f"Found {num_duplicates} duplicate rows (excluding CALVALUS_ID).")

# Remove duplicates based on all columns except CALVALUS_ID
df_cleaned = df.drop_duplicates(subset=df.columns.difference(["CALVALUS_ID"]))
print(f"After removing duplicates: {len(df_cleaned)} rows remain.")

# === 3. Define Sentinel-3 flags to mask ===
mask_patterns = [
    "quality_flags.invalid",
    "quality_flags.cosmetic",
    "quality_flags.duplicated",
    "quality_flags.sun_glint_risk",
    "quality_flags.straylight_risk",
    "quality_flags.saturated_",
    "pixel_classif_flags.IDEPIX_INVALID",
    "pixel_classif_flags.IDEPIX_CLOUD",
    "pixel_classif_flags.IDEPIX_CLOUD_SHADOW",
    "pixel_classif_flags.IDEPIX_SNOW_ICE",
    "pixel_classif_flags.IDEPIX_MOUNTAIN_SHADOW",
    "c2rcc_flags.Rtosa_OOS",
    "c2rcc_flags.Rhow_OOS",
    "c2rcc_flags.Iop_OOR",
    "c2rcc_flags.Rhow_OOR",
    "c2rcc_flags.*_at_max",
    "c2rcc_flags.*_at_min",
    "c2rcc_flags.Cloud_risk",
    "mph_chl_flags.mph_adjacency",
]

# === 4. Identify flag columns matching any pattern ===
bad_flag_cols = [
    col for col in df_cleaned.columns
    if any(re.search(pat.replace("*", ".*"), col) for pat in mask_patterns)
]

print(f"Applying mask using {len(bad_flag_cols)} flag columns.")

# === 5. Keep only good pixels (no bad flags set) ===
good_mask = (df_cleaned[bad_flag_cols].sum(axis=1) == 0)
df_flagged_clean = df_cleaned[good_mask].copy()
print(f"After applying flags: {len(df_flagged_clean)} valid rows remain.")

# === 7. Save final cleaned dataset ===
output_path = (
    "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixel_clean_correlation.xlsx"
)
df_flagged_clean.to_excel(output_path, index=False)
print(f"Cleaned file saved as '{output_path}'")
