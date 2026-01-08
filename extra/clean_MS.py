import pandas as pd

# -----------------------------
# Input and output file paths
# -----------------------------
input_file = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/marine_stations_sognefjord_vannmiljo_2016_2025.xlsx"
output_file = "VT16_marinestation_data.xlsx"

# -----------------------------
# Read the sheet you want to filter
# -----------------------------
# Replace "Stations" with the sheet name that has the "Station code" column
df = pd.read_excel(input_file, sheet_name="Water chemistry")

# -----------------------------
# Keep only rows where 'Station code' == 'VT16'
# -----------------------------
df_filtered = df[df["Station code"] == "VT16"]

# -----------------------------
# Save the filtered data to a new Excel file
# -----------------------------
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_filtered.to_excel(writer, sheet_name="Stations", index=False)

print(f"Filtered Excel file saved as '{output_file}' with only 'VT16' stations.")
