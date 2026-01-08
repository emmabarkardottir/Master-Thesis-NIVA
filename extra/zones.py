import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from netCDF4 import Dataset
import geopandas as gpd
from shapely.geometry import Point
import math

param_info = {
    "conc_chl_mean": {
        "label": "Chlorophyll-a concentration",
        "units": "mg m$^{-3}$",
    },
    "iop_adg_mean": {
        "label": "CDOM + detritus absorption (a$_{dg}$)",
        "units": "m$^{-1}$",
    },
    "kd489_mean": {
        "label": "Diffuse attenuation coefficient Kd(489)",
        "units": "m$^{-1}$",
    },
    "c2rcc_secchi_depth_3_mean": {
        "label": "Secchi depth",
        "units": "m",
    },
    "spm_nechad_665_mean": {
        "label": "SPM (Nechad 665)",
        "units": "g m$^{-3}$",
    },
    "spm_nechad_865_mean": {
        "label": "SPM (Nechad 865)",
        "units": "g m$^{-3}$",
    },
    "tur_nechad_665_mean": {
        "label": "Turbidity (Nechad 665)",
        "units": "FNU",
    },
    "tur_nechad_865_mean": {
        "label": "Turbidity (Nechad 865)",
        "units": "FNU",
    },
    "chl_c2rcc_mean": {
        "label": "Chlorophyll-a (C2RCC)",
        "units": "mg m$^{-3}$",
    },
}

main_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3_daily"
zones_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/shapefile_zones/zones_sognefjorden.shp"
plot_output = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/zone_plots"
os.makedirs(plot_output, exist_ok=True)


zones_gdf = gpd.read_file(zones_path)
zones_gdf = zones_gdf[~zones_gdf.geometry.isnull()].reset_index(drop=True)

if zones_gdf.crs is None or zones_gdf.crs.to_epsg() != 4326:
    zones_gdf = zones_gdf.to_crs(epsg=4326)

zone_names = [
    zone.get("zone_name", f"Zone_{i+1}")
    for i, zone in zones_gdf.iterrows()
]

n_zones = len(zone_names)

# --------------------------------------------------
# LOOP OVER PARAMETERS
# --------------------------------------------------

for param_name, meta in param_info.items():

    print(f"Processing parameter: {param_name}")

    data_list = []
    time_list = []
    lat, lon = None, None

    # ----------------------------------------------
    # READ NETCDF FILES
    # ----------------------------------------------

    for root, _, files in os.walk(main_folder):
        for f in sorted(files):
            if not f.endswith(".nc"):
                continue

            match = re.search(r"(\d{8})(?=\.nc$)", f)
            if match is None:
                continue

            try:
                file_date = pd.to_datetime(match.group(1), format="%Y%m%d")
            except ValueError:
                continue

            fpath = os.path.join(root, f)

            try:
                with Dataset(fpath, "r") as ds:
                    if param_name not in ds.variables:
                        continue

                    arr = np.array(ds.variables[param_name][:], dtype=float)

                    if lat is None and "lat" in ds.variables and "lon" in ds.variables:
                        lat = np.array(ds.variables["lat"][:])
                        lon = np.array(ds.variables["lon"][:])

                    if arr.ndim == 3:
                        for i in range(arr.shape[0]):
                            data_list.append(arr[i])
                            time_list.append(file_date)
                    elif arr.ndim == 2:
                        data_list.append(arr)
                        time_list.append(file_date)

            except Exception as e:
                print(f"Skipped {fpath}: {e}")

    if len(data_list) == 0:
        print(f"No data for {param_name}")
        continue

    data_stack = np.stack(data_list)
    lon2d, lat2d = np.meshgrid(lon, lat)

    # ----------------------------------------------
    # ZONE MEDIANS
    # ----------------------------------------------

    zone_medians = {}

    for idx, zone in zones_gdf.iterrows():
        zone_name = zone_names[idx]

        if zone.geometry is None or zone.geometry.is_empty:
            continue

        mask = np.array(
            [zone.geometry.contains(Point(x, y))
             for x, y in zip(lon2d.ravel(), lat2d.ravel())]
        ).reshape(lon2d.shape)

        if not mask.any():
            continue

        masked = np.where(mask, data_stack, np.nan)
        zone_medians[zone_name] = np.nanmedian(masked, axis=(1, 2))

    # ----------------------------------------------
    # TIME SERIES DATAFRAME
    # ----------------------------------------------

    time_series = pd.to_datetime(pd.Series(time_list), errors="coerce")
    zone_df = pd.DataFrame(zone_medians)
    zone_df = zone_df.iloc[:len(time_series)]
    zone_df.index = time_series
    zone_df = zone_df.sort_index()
    zone_df = zone_df.dropna(how="all")

    if zone_df.empty:
        print(f"No valid zone data for {param_name}")
        continue

    # ----------------------------------------------
    # MULTI-PANEL PLOTTING (ONE FIGURE)
    # ----------------------------------------------

    ncols = 2
    nrows = math.ceil(n_zones / ncols)

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(14, 4 * nrows),
        sharex=True
    )

    axes = axes.flatten()

    for i, zone in enumerate(zone_df.columns):
        ax = axes[i]

        ax.plot(
            zone_df.index,
            zone_df[zone],
            "o",
            markersize=3,
            alpha=0.6,
            color="blue",
            label="Daily median"
        )

        rolling_median = zone_df[zone].rolling(
            window=90,
            min_periods=1,
            center=True
        ).median()

        ax.plot(
            rolling_median.index,
            rolling_median,
            color="red",
            linewidth=2,
            label="90-day rolling median"
        )

        ax.set_title(zone)
        ax.set_ylabel(f"{meta['label']} [{meta['units']}]")
        ax.grid(True, linestyle="--", alpha=0.4)

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

        if i == 0:
            ax.legend()

    # Turn off unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    fig.suptitle(
        f"Temporal evolution of {meta['label']} "
        f"in Sognefjorden zones (Sentinel-3)",
        fontsize=16,
        fontweight="bold"
    )

    fig.autofmt_xdate()
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    save_path = os.path.join(
        plot_output,
        f"{param_name}_zones_timeseries.png"
    )
    fig.savefig(save_path, dpi=300)
    plt.close(fig)

    print(f"Saved figure: {save_path}")

print("All parameters processed successfully.")
