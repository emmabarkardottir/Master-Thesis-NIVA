import os
import numpy as np
import xarray as xr
from netCDF4 import Dataset
import matplotlib.pyplot as plt

choice = 1  # Change this number to select a parameter

param = {
    1: "conc_chl_mean",
    2: "iop_adg_mean",
    3: "kd489_mean",
    4: "c2rcc_secchi_depth_3_mean",
    5: "spm_nechad_665_mean",
    6: "spm_nechad_865_mean",
    7: "tur_nechad_665_mean",
    8: "tur_nechad_865_mean",
    9: "chl_c2rcc_mean",
}

param_name = param[choice]
print(f"Selected parameter: {param_name}")

main_folder = ("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3_daily")
plot_output = ("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/avg_plots")

# Read all NetCDF files
data_list = []
lat, lon = None, None

for root, _, files in os.walk(main_folder):
    for f in files:
        if f.endswith(".nc"):
            fpath = os.path.join(root, f)
            try:
                with Dataset(fpath, mode="r") as ds:
                    arr = ds.variables[param_name][:].astype(float)

                    if lat is None and "lat" in ds.variables and "lon" in ds.variables:
                        lat = ds.variables["lat"][:]
                        lon = ds.variables["lon"][:]

                    data_list.append(arr)

            except Exception as e:
                print(f"Skipped {fpath}: {e}")

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

# Plot mean and standard deviation maps
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

mean_da.plot(
    ax=axes[0],
    cmap="viridis",
    vmin=0,
    vmax=7,
    cbar_kwargs={"label": "units?"},  # Change units if needed
)
axes[0].set_title(f"Average {param_name}")

std_da.plot(
    ax=axes[1],
    cmap="magma",
    vmin=0,
    vmax=15,
    cbar_kwargs={"label": "units?"},  # Change units if needed
)
axes[1].set_title(f"Standard Deviation of {param_name}")

plt.tight_layout()

filename = f"{param_name}_summary.png"
plt.savefig(os.path.join(plot_output, filename), dpi=300)
plt.show()

print(f"Figure saved to: {plot_output}")
