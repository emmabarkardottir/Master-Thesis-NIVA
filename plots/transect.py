import os
import glob
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from pyproj import Geod
import re
from datetime import datetime

DATA_ROOT = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3_daily"
TRANSECT_CSV = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/transect/transect_points.csv"
VAR = "tur_nechad_865_mean"
UNIT = "FNU"
YEAR = "2020"

df = pd.read_csv(TRANSECT_CSV)
lats_transect = df["latitude"].values
lons_transect = df["longitude"].values

year_folder = os.path.join(DATA_ROOT, YEAR)
files = sorted(glob.glob(os.path.join(year_folder, "*.nc")))

print(f"Processing year {YEAR}: {len(files)} files found.")

# Compute cumulative distances along your GIS-defined transect (in km)
geod = Geod(ellps="WGS84")
distances = [0]

for i in range(1, len(lats_transect)):
    _, _, d = geod.inv(lons_transect[i-1], lats_transect[i-1],
                       lons_transect[i],   lats_transect[i])
    distances.append(distances[-1] + d/1000.0)

distances = np.array(distances)
print(f"Loaded user-defined transect with {len(distances)} points, total length {distances[-1]:.2f} km")

# date from filename
def extract_date_from_filename(filename):
    try:
        date_str = re.search(r"\d{8}", filename).group(0)
        return datetime.strptime(date_str, "%Y%m%d")
    except:
        print(f"Could not extract date from {filename}")
        return None

# extract transect data from a single file
def extract_transect_TSM(ncfile):
    date = extract_date_from_filename(os.path.basename(ncfile))
    if date is None:
        return None

    try:
        ds = xr.open_dataset(ncfile)
    except:
        print(f"Could not open: {ncfile}")
        return None

    if VAR not in ds:
        print(f"Variable '{VAR}' not found in {ncfile}")
        ds.close()
        return None

    lat = ds["lat"].values
    lon = ds["lon"].values
    tsm = ds[VAR].values

    # If lat/lon are 1D, expand to 2D
    if lat.ndim == 1 and lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)

    # KD-tree nearest-neighbor extraction
    points = np.column_stack((lat.ravel(), lon.ravel()))
    tree = cKDTree(points)

    _, idx = tree.query(np.column_stack((lats_transect, lons_transect)))
    tsm_profile = tsm.ravel()[idx]

    ds.close()
    return date, tsm_profile


# time x space arrays
times = []
transect_values = []

for f in files:
    res = extract_transect_TSM(f)
    if res:
        t, profile = res
        times.append(t)
        transect_values.append(profile)

times = np.array(times)
transect_values = np.array(transect_values)

order = np.argsort(times)
times = times[order]
transect_values = transect_values[order]

# Plot
df_temp = pd.DataFrame(transect_values)
temp_smooth = df_temp.rolling(7, center=True, min_periods=1).median().values

plt.figure(figsize=(14, 6))
plt.pcolormesh(times, distances, temp_smooth.T, 
               shading="auto", vmin=0, vmax=2)
plt.colorbar(label= f"{UNIT}")
plt.xlabel("Date")
plt.ylabel("Distance along transect (km)")
plt.title(f"Sognefjorden Transect ({VAR} - {YEAR})")
plt.tight_layout()

# save plot 
output_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/transects"
output_plot = os.path.join(output_path, f"transect_{VAR}_{YEAR}.png")
plt.savefig(output_plot, dpi=300)
print(f"Plot saved to {output_plot}")

plt.show()