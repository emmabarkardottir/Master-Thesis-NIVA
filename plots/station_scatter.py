import pandas as pd
import matplotlib.pyplot as plt
import os


choice = 1
STATIONS = {
    1: "VT12",
    2: "VT16",
    3: "VT79",
}
station_name = STATIONS[choice]

file1 = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx"
file2 = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/Sentinel3_pixel_clean.xlsx"


df1 = pd.read_excel(file1)
df2 = pd.read_excel(file2)

time_col1 = "Prøvetakingstidspunkt"
time_col2 = "pixel_time"

df1[time_col1] = pd.to_datetime(df1[time_col1], errors="coerce")
df2[time_col2] = pd.to_datetime(df2[time_col2], errors="coerce")

df1 = df1[
    (df1["Nedre dyp"] >= 0) & (df1["Nedre dyp"] <= 5)]

df1_station = df1[df1["s"] == station_name].copy()
df2_station = df2[df2["Name"] == station_name].copy()

param_map = {
    "CDOM": "iop_adg_mean",
    "TSM": "spm_nechad_865_mean",
    "TURB": "tur_nechad_865_mean",
    "KLFA": "conc_chl_mean",
    "SECCI": "c2rcc_secchi_depth_3_mean",
}

param_units = {
    "CDOM": r"m$^{-1}$",
    "TSM": r"g m$^{-3}$",
    "TURB": r"FNU",
    "KLFA": r"mg m$^{-3}$",
    "SECCI": r"m",
}


# Determine which parameters to plot
params_to_plot = [
    p for p in param_map.keys()
    if (p in df1_station.columns and not df1_station[p].dropna().empty)
    or (param_map[p] in df2_station.columns and not df2_station[param_map[p]].dropna().empty)
]

# Plot
if params_to_plot:
    n = len(params_to_plot)
    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 5 * nrows))
    axes = axes.flatten()

    colors = ["tab:blue", "tab:orange"]

    for i, param in enumerate(params_to_plot):
        ax = axes[i]
        param_sat = param_map[param]

        # In situ
        if param in df1_station.columns:
            subset1 = df1_station.dropna(subset=[param])
            ax.scatter(
                subset1[time_col1],
                subset1[param],
                s=10,
                color=colors[0],
                label="In situ"
            )

        # Satellite
        if param_sat in df2_station.columns:
            subset2 = df2_station.dropna(subset=[param_sat, time_col2])
            if not subset2.empty:
                ax.scatter(
                    subset2[time_col2],
                    subset2[param_sat],
                    s=10,
                    color=colors[1],
                    label="Sentinel-3"
                )

        # Labels
        unit = param_units.get(param, "")
        ylabel = f"{param} ({unit})" if unit else param

        ax.set_title(param)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Time")
        ax.tick_params(axis="x", rotation=45)
        ax.legend()

    # Hide unused axes
    for j in range(len(params_to_plot), len(axes)):
        axes[j].axis("off")

    fig.suptitle(
        f"Timeseries plots for station {station_name} — In situ vs Sentinel-3",
        fontsize=16
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

    output_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/timeseries"
    os.makedirs(output_folder, exist_ok=True)

    filename = f"timeseries_conc_{station_name}.png"
    fig.savefig(os.path.join(output_folder, filename), dpi=300)
    print(f"Saved plot figure: {filename}")
