import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

root_dir = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3_daily"
plot_output = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/avg_plots"
os.makedirs(plot_output, exist_ok=True)

chlorophyll_values = []

for subdir, dirs, files in os.walk(root_dir):
    for filename in files:
        if filename.endswith(".nc"):
            file_path = os.path.join(subdir, filename)
            ds = xr.open_dataset(file_path)

            if "chl_c2rcc_mean" in ds.variables:
                chl = ds["chl_c2rcc_mean"].values
                chlorophyll_values.append(chl.flatten())

chlorophyll_values = np.concatenate(chlorophyll_values)
chlorophyll_values = chlorophyll_values[~np.isnan(chlorophyll_values)]

lower_percentile = 1
upper_percentile = 99

low_thresh = np.percentile(chlorophyll_values, lower_percentile)
high_thresh = np.percentile(chlorophyll_values, upper_percentile)

filtered_chl = chlorophyll_values[
    (chlorophyll_values >= low_thresh) &
    (chlorophyll_values <= high_thresh)
]

print(f"Removed values below {low_thresh:.4f} and above {high_thresh:.4f}")
print(f"Remaining observations: {filtered_chl.size:,}")

# plotting
plt.figure(figsize=(8,5))
plt.hist(filtered_chl, bins=50)
plt.xlabel("Chlorophyll concentration")
plt.ylabel("Number of observations")
plt.title(f"Histogram of Chlorophyll ({lower_percentile}-{upper_percentile}th percentiles)")
plt.grid(True)
plt.show()
