import os
import re
import numpy as np
import xarray as xr
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from datetime import datetime

param_info = {
    "conc_chl_mean": {
        "label": "Chlorophyll-a concentration",
        "units": "mg m$^{-3}$",
        "vmin_mean": 0,
        "vmax_mean": 7,
        "vmin_std": 0,
        "vmax_std": 14,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "iop_adg_mean": {
        "label": "CDOM + detritus absorption (a$_{dg}$)",
        "units": "m$^{-1}$",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 7,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "kd489_mean": {
        "label": "Diffuse attenuation coefficient Kd(489)",
        "units": "m$^{-1}$",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 7,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "c2rcc_secchi_depth_3_mean": {
        "label": "Secchi depth",
        "units": "m",
        "vmin_mean": 0,
        "vmax_mean": 20,
        "vmin_std": 0,
        "vmax_std": 20,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "spm_nechad_665_mean": {
        "label": "SPM (Nechad 665)",
        "units": "g m$^{-3}$",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 2,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "spm_nechad_865_mean": {
        "label": "SPM (Nechad 865)",
        "units": "g m$^{-3}$",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 5,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "tur_nechad_665_mean": {
        "label": "Turbidity (Nechad 665)",
        "units": "FNU",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 2,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "tur_nechad_865_mean": {
        "label": "Turbidity (Nechad 865)",
        "units": "FNU",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 5,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
    "chl_c2rcc_mean": {
        "label": "Chlorophyll-a (C2RCC)",
        "units": "mg m$^{-3}$",
        "vmin_mean": 0,
        "vmax_mean": 2,
        "vmin_std": 0,
        "vmax_std": 2,
        "cmap_mean": "viridis",
        "cmap_std": "magma",
    },
}

main_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3_daily"
plot_output = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/avg_plots/test"
os.makedirs(plot_output, exist_ok=True)

seasons = {
    "Spring Bloom (Mar–Apr)": [3, 4],
    "Summer (May–Aug)": [5, 6, 7, 8],
    "Autumn (Sep–Oct)": [9, 10],
}

# LOOP OVER PARAMETERS
for param_name, meta in param_info.items():

    print(f"Processing seasonal plots for: {param_name}")

    seasonal_data = {season: [] for season in seasons}
    lat, lon = None, None

    for root, _, files in os.walk(main_folder):
        for f in files:
            if not f.endswith(".nc"):
                continue

            # Extract date from filename
            try:
                date_str = re.search(r"\d{8}", f).group(0)
                file_date = datetime.strptime(date_str, "%Y%m%d")
            except Exception:
                continue

            fpath = os.path.join(root, f)

            try:
                with Dataset(fpath, mode="r") as ds:
                    if param_name not in ds.variables:
                        continue

                    arr = ds.variables[param_name][:].astype(float)

                    if lat is None and "lat" in ds.variables and "lon" in ds.variables:
                        lat = ds.variables["lat"][:]
                        lon = ds.variables["lon"][:]

                    for season_name, months in seasons.items():
                        if file_date.month in months:
                            seasonal_data[season_name].append(arr)

            except Exception as e:
                print(f"Skipped {fpath}: {e}")


    # COMPUTE SEASONAL STATS
    seasonal_mean = {}
    seasonal_std = {}

    for season_name, data_list in seasonal_data.items():
        if len(data_list) == 0:
            print(f"⚠️ No data for {season_name} ({param_name})")
            continue

        stack = np.stack(data_list)
        seasonal_mean[season_name] = np.nanmean(stack, axis=0)
        seasonal_std[season_name] = np.nanstd(stack, axis=0)

    if not seasonal_mean:
        print(f" No seasonal data found for {param_name}")
        continue

    # PLOTTING
    fig, axes = plt.subplots(3, 2, figsize=(15, 15))

    for i, season_name in enumerate(seasons.keys()):

        if season_name not in seasonal_mean:
            axes[i, 0].axis("off")
            axes[i, 1].axis("off")
            continue

        mean_da = xr.DataArray(
            seasonal_mean[season_name],
            dims=("lat", "lon"),
            coords={"lat": lat, "lon": lon},
        )

        std_da = xr.DataArray(
            seasonal_std[season_name],
            dims=("lat", "lon"),
            coords={"lat": lat, "lon": lon},
        )

        mean_da.plot(
            ax=axes[i, 0],
            cmap="viridis",
            vmin=meta["vmin_mean"],
            vmax=meta["vmax_mean"],
            cbar_kwargs={"label": meta["units"]},
        )
        axes[i, 0].set_title(f"{season_name} – Mean {meta['label']}")

        std_da.plot(
            ax=axes[i, 1],
            cmap="magma",
            vmin=meta["vmin_std"],
            vmax=meta["vmax_std"],
            cbar_kwargs={"label": meta["units"]},
        )
        axes[i, 1].set_title(f"{season_name} – Std {meta['label']}")

    plt.tight_layout()
    outfile = os.path.join(plot_output, f"{param_name}_seasonal_mean_std.png")
    plt.savefig(outfile, dpi=300)
    plt.close()

    print(f"Saved: {outfile}")

print(" All seasonal plots completed.")
