import pandas as pd
import glob
import os

# Folder containing all your Excel files
folder_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/NVE_data/discharge"

# Get all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

# List to hold data from each file
dataframes = []

# Loop through each file and read it
for file in csv_files:
    df = pd.read_csv(file)
    df['Source_File'] = os.path.basename(file)  # optional: keep track of source
    dataframes.append(df)

# Concatenate all DataFrames
merged_df = pd.concat(dataframes, ignore_index=True)

# Save to a new CSV file
output_file = "NVE_discharge_merged.csv"
merged_df.to_csv(output_file, index=False)

print(f"Merged {len(csv_files)} files into {output_file}")