import pandas as pd
import glob
import os
import matplotlib.pyplot as plt

data_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/NVE_data/discharge/"
plot_folder = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/plots/cumulative"
os.makedirs(plot_folder, exist_ok=True)

csv_files = glob.glob(os.path.join(data_folder, "*.csv"))

all_data = []

for file in csv_files:
    station_name = os.path.splitext(os.path.basename(file))[0]

    try:
        df = pd.read_csv(file)
        df["datetime"] = pd.to_datetime(df["datetime"])

        # filter years
        df = df[(df["datetime"].dt.year >= 2018) & (df["datetime"].dt.year <= 2023)]
        if df.empty:
            continue

        df["station"] = station_name
        df["year"] = df["datetime"].dt.year
        df["day_of_year"] = df["datetime"].dt.dayofyear
        df["month"] = df["datetime"].dt.month

        # cumulative discharge per station per year
        df["cumulative_discharge"] = (
            df.groupby(["station", "year"])["value"].cumsum()
        )

        all_data.append(df)

    except Exception as e:
        print(f"Error processing file {file}: {e}")

df_all = pd.concat(all_data, ignore_index=True)

#  statistics
df_summary = (
    df_all.groupby(["year", "day_of_year"])["cumulative_discharge"]
    .mean()
    .reset_index()
)

yearly_totals_all = df_all.groupby("year")["value"].sum()

# consistent colors per year
distinct_colors = ["#076C4E", "#d95f02", "#7570b3", "#e7298a", "#7acf18", "#e6ab02"]
years = sorted(yearly_totals_all.index)
year_color_map = dict(zip(years, distinct_colors))


# PLOT 1 — CUMULATIVE DISCHARGE
plt.figure(figsize=(14, 6))

for year, group in df_summary.groupby("year"):
    plt.plot(
        group["day_of_year"],
        group["cumulative_discharge"],
        label=f"{year} ({yearly_totals_all[year]:.0f})",
        color=year_color_map[year],
        linewidth=2,
    )

plt.xlabel("Day of Year (1–365)")
plt.ylabel("Average cumulative discharge (m³/s·day)")
plt.title("Yearly cumulative freshwater discharge (2018–2023, all stations)")
plt.legend(
    title="Year (total discharge - m³/s)",
    bbox_to_anchor=(1.05, 1),
    loc="upper left",
)
plt.tight_layout()

save_path = os.path.join(plot_folder, "cumulative_discharge_by_year.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"Saved: {save_path}")

# PLOT 2 — TOTAL YEARLY DISCHARGE (BAR)
plt.figure(figsize=(8, 5))
plt.bar(yearly_totals_all.index, yearly_totals_all.values)

plt.ylabel("Total annual discharge (m³/s·day)")
plt.xlabel("Year")
plt.title("Total yearly freshwater discharge per year (2018–2023)")
plt.tight_layout()

save_path = os.path.join(plot_folder, "total_yearly_discharge_bar.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"Saved: {save_path}")

# PLOT 3 — MEAN DAILY DISCHARGE (NON-CUMULATIVE)
df_mean_daily = (
    df_all.groupby(["year", "day_of_year"])["value"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(14, 6))

for year, group in df_mean_daily.groupby("year"):
    plt.plot(
        group["day_of_year"],
        group["value"],
        label=f"{year}",
        color=year_color_map[year],
        linewidth=2,
    )

plt.xlabel("Day of year (1–365)")
plt.ylabel("Mean daily discharge (m³/s)")
plt.title("Mean daily freshwaterdischarge by year (2018–2023, all stations)")
plt.legend(
    title="Year",
    bbox_to_anchor=(1.05, 1),
    loc="upper left",
)
plt.tight_layout()

save_path = os.path.join(plot_folder, "mean_daily_discharge_by_year.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"Saved: {save_path}")

print("All discharge plots saved successfully.")
