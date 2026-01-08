import pandas as pd
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
import cartopy.crs as ccrs

# Marine stations
file_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/stations_S3_Vestland_coast_selected_valid_red_clean.xlsx"
df = pd.read_excel(file_path)

stations_of_interest = ["VT12", "VT16", "VT79", "VT Extra"]
df_marine = df[df["Name"].isin(stations_of_interest)].dropna(subset=["Lat", "Lon"])
df_marine["Type"] = "Marine"

manual_marine_stations = pd.DataFrame({
    "Name": ["VT Extra1", "VT Extra2"],
    "Lat": [61.186101, 61.365111],
    "Lon": [7.434517, 7.371556],
    "Type": ["Marine", "Marine"]
})

existing_names = df_marine["Name"].tolist()
manual_marine_stations = manual_marine_stations[~manual_marine_stations["Name"].isin(existing_names)]
df_marine = pd.concat([df_marine, manual_marine_stations], ignore_index=True)

# NVE discharge stations 
df_discharge = pd.read_csv("/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/NVE_data/discharge_stations_metadata.csv")
df_discharge = df_discharge.dropna(subset=["latitude", "longitude"])
df_discharge = df_discharge.rename(columns={"latitude": "Lat", "longitude": "Lon"})
df_discharge["Type"] = "NVE Discharge"

# Set up projection
proj = ccrs.UTM(33)
fig, axes = plt.subplots(2, 1, figsize=(8, 8), subplot_kw={'projection': proj})
extent = [3.5, 9, 60.5, 61.5]

# Data to plot
station_data = [
    ("Marine Stations", df_marine, {"Marine": "red"}),
    ("NVE Discharge Stations", df_discharge, {"NVE Discharge": "blue"})
]

for ax, (title, df_plot, colors) in zip(axes, station_data):
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.add_feature(cfeature.LAKES, facecolor="lightblue", alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)

    for station_type, group in df_plot.groupby("Type"):
        ax.scatter(group["Lon"], group["Lat"], 
                   c=colors[station_type], s=50, edgecolor="black",
                   transform=ccrs.PlateCarree(), label=station_type)
        
        label_col = "Name" if "Name" in group.columns else "station_name"
        for lon, lat, name in zip(group["Lon"], group["Lat"], group[label_col]):
            ax.text(lon + 0.03, lat + 0.03, str(name),
                    transform=ccrs.PlateCarree(), fontsize=7)
    
    ax.set_title(title, fontsize=11)
    ax.legend(loc="lower left", fontsize=8)

plt.tight_layout(pad=2.0)

# Save figure
output_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/marine_discharge_stations.png"
plt.savefig(output_path, dpi=300) 

plt.show()
