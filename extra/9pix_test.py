import os
import re
import numpy as np
import pandas as pd
from netCDF4 import Dataset

main_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3_daily"

target_lat = 61.365111
target_lon = 7.371556
window_size = 3
half_window = window_size // 2

# Parameters for combined mask
PARAMETERS = [
    "conc_chl_mean",
    "conc_tsm_mean",
    "iop_adg_mean",
    "kd489_mean",
    "c2rcc_secchi_depth_3_mean",
    "spm_nechad_665_mean",
    "spm_nechad_865_mean",
    "tur_nechad_665_mean",
    "tur_nechad_865_mean",
    "chl_c2rcc_mean",
]

records = []

for root, _, files in os.walk(main_folder):
    for f in sorted(files):
        if not f.endswith(".nc"):
            continue

        fpath = os.path.join(root, f)

        # Extract date from filename
        match = re.search(r"(\d{8})", f)
        date = pd.to_datetime(match.group(1), format="%Y%m%d") if match else None

        try:
            with Dataset(fpath) as ds:
                lat = ds.variables["lat"][:]
                lon = ds.variables["lon"][:]

                combined_mask = None

                # Build combined mask across all parameters
                for vname in PARAMETERS:
                    if vname not in ds.variables:
                        print(f"Warning: {vname} not found in {f}")
                        continue

                    data = ds.variables[vname][:]
                    if data.ndim == 3:
                        data = data[0, :, :]  # take first time slice
                    elif data.ndim > 3:
                        raise ValueError(f"Unexpected dimensions for {vname}: {data.shape}")

                    if np.ma.is_masked(data):
                        data = data.filled(np.nan)

                    valid = np.isfinite(data)
                    if combined_mask is None:
                        combined_mask = valid.copy()
                    else:
                        combined_mask &= valid

                # Target pixel window
                lat_idx = np.argmin(np.abs(lat - target_lat))
                lon_idx = np.argmin(np.abs(lon - target_lon))

                lat_slice = slice(max(lat_idx - half_window, 0), min(lat_idx + half_window + 1, len(lat)))
                lon_slice = slice(max(lon_idx - half_window, 0), min(lon_idx + half_window + 1, len(lon)))

                mask_patch = combined_mask[lat_slice, lon_slice]

                if not np.any(mask_patch):
                    print(f"{f}: 0.0% valid pixels in window (skipped)")
                    continue

                # % valid pixels within box
                valid_pct_patch = np.mean(mask_patch) * 100
                print(f"{f}: {valid_pct_patch:.1f}% valid pixels in window")

                valid_rows = np.any(mask_patch, axis=1)
                valid_cols = np.any(mask_patch, axis=0)
                n_valid_lat = np.sum(valid_rows)
                n_valid_lon = np.sum(valid_cols)

                lat_sub = lat[lat_slice]
                lon_sub = lon[lon_slice]
                lon_grid, lat_grid = np.meshgrid(lon_sub, lat_sub)

                valid_lats = lat_grid[mask_patch]
                valid_lons = lon_grid[mask_patch]

                mean_lat = np.mean(valid_lats)
                sigma_lat = np.std(valid_lats)
                mean_lon = np.mean(valid_lons)
                sigma_lon = np.std(valid_lons)

                # --- Extract SPM parameters ---
                spm_665_mean = np.nan
                spm_665_sigma = np.nan
                spm_865_mean = np.nan
                spm_865_sigma = np.nan

                if "spm_nechad_665_mean" in ds.variables:
                    spm_665_data = ds.variables["spm_nechad_665_mean"][:]
                    if spm_665_data.ndim == 3:
                        spm_665_data = spm_665_data[0, :, :]
                    if np.ma.is_masked(spm_665_data):
                        spm_665_data = spm_665_data.filled(np.nan)
                    spm_665_patch = spm_665_data[lat_slice, lon_slice][mask_patch]
                    spm_665_mean = np.nanmean(spm_665_patch)
                    spm_665_sigma = np.nanstd(spm_665_patch)

                if "spm_nechad_865_mean" in ds.variables:
                    spm_865_data = ds.variables["spm_nechad_865_mean"][:]
                    if spm_865_data.ndim == 3:
                        spm_865_data = spm_865_data[0, :, :]
                    if np.ma.is_masked(spm_865_data):
                        spm_865_data = spm_865_data.filled(np.nan)
                    spm_865_patch = spm_865_data[lat_slice, lon_slice][mask_patch]
                    spm_865_mean = np.nanmean(spm_865_patch)
                    spm_865_sigma = np.nanstd(spm_865_patch)

                # --- Append record ---
                if date is not None:
                    records.append((
                        date,
                        target_lat,
                        target_lon,
                        n_valid_lat,
                        n_valid_lon,
                        mean_lat,
                        sigma_lat,
                        mean_lon,
                        sigma_lon,
                        valid_pct_patch,
                        spm_665_mean,
                        spm_665_sigma,
                        spm_865_mean,
                        spm_865_sigma,
                    ))

        except Exception as e:
            print(f"Skipped {fpath}: {e}")

# === BUILD OUTPUT TABLE ===
df = pd.DataFrame(
    records,
    columns=[
        "pixel_time",
        "target_latitude",
        "target_longitude",
        "n_valid_latitude",
        "n_valid_longitude",
        "mean_latitude",
        "sigma_latitude",
        "mean_longitude",
        "sigma_longitude",
        "valid_pct_in_window",
        "spm_nechad_665_mean",
        "spm_nechad_665_sigma",
        "spm_nechad_865_mean",
        "spm_nechad_865_sigma",
    ]
)

df = df.sort_values("pixel_time").reset_index(drop=True)

# === SAVE RESULTS ===
output_dir = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "pixel_VTextra.csv")

df.to_csv(output_file, index=False)
print(f"\n Saved results to '{output_file}'")
