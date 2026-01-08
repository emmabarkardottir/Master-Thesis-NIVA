import os
import numpy as np
import xarray as xr
from netCDF4 import Dataset
import matplotlib.pyplot as plt

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


# LOOP OVER PARAMETERS
for param_name, meta in param_info.items():

    print(f"Processing: {param_name}")

    data_list = []
    lat, lon = None, None

    # Read NetCDF files
    for root, _, files in os.walk(main_folder):
        for f in files:
            if not f.endswith(".nc"):
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

                    data_list.append(arr)

            except Exception as e:
                print(f"Skipped {fpath}: {e}")

    if len(data_list) == 0:
        print(f"No data found for {param_name}, skipping.")
        continue

    data_stack = np.stack(data_list)
    data_mean = np.nanmean(data_stack, axis=0)
    data_std = np.nanstd(data_stack, axis=0)

    mean_da = xr.DataArray(
        data_mean,
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": lon},
        name=param_name,
    )

    std_da = xr.DataArray(
        data_std,
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": lon},
        name=f"{param_name}_std",
    )

    # PLOTTING
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    mean_da.plot(
        ax=axes[0],
        cmap=meta["cmap_mean"],
        vmin=meta["vmin_mean"],
        vmax=meta["vmax_mean"],
        cbar_kwargs={"label": meta["units"]},
    )
    axes[0].set_title(f"Mean {meta['label']}")

    std_da.plot(
        ax=axes[1],
        cmap=meta["cmap_std"],
        vmin=meta["vmin_std"],
        vmax=meta["vmax_std"],
        cbar_kwargs={"label": meta["units"]},
    )
    axes[1].set_title(f"Standard deviation of {meta['label']}")

    plt.tight_layout()

    outfile = os.path.join(plot_output, f"{param_name}_mean_std.png")
    plt.savefig(outfile, dpi=300)
    plt.close()

    print(f"Saved: {outfile}")

print("All parameters processed.")
