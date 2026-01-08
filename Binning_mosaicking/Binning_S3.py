# import relevant packages
import numpy as np
import os
from os.path import exists
import subprocess
from datetime import datetime
import shutil
import argparse 
import csv
import glob

#add by Emma for command line arguments

parser = argparse.ArgumentParser(description='Binning of S3 data to L3')
parser.add_argument('--wkd', '-w', action='store', default='Binning_mosaicking', help="Path to the working directory")

parser.add_argument('--srcdir', '-s', action='store', required=True, help="Path to the source directory")

parser.add_argument('--trgdir', '-t', action='store', default='L3', help="Path to the target directory")

parser.add_argument('--xmlfile', '-x', action='store', default= 'S3_L3binning_idepix_c2rcc.xml', help='Path to the xml file for binning')

parser.add_argument('--area', '-a', action='store', default= "Sognefjorden", help="Area for binning, e.g. Sognefjorden")

parser.add_argument('--year', '-y', action='store', required=True, help="Year for binning, format YYYY")

parser.add_argument('--month', '-m', action='store', required=True, help="Month for binning, format MM")

parser.add_argument('--day', '-d', action='store', required=True, help="Day for binning, format DD")

args = parser.parse_args()


#Specify working directory and script source
# wkd   = '/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/code/Binning_mosaicking'
# xmlfile = f'{wkd}/S3_L3binning_idepix_c2rcc.xml'
# trgdir = f'/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/code/L3'
wkd   = args.wkd
xmlfile = os.path.join(wkd, args.xmlfile)
trgdir = args.trgdir
srcdir = args.srcdir
area = args.area
if not os.path.exists(trgdir):
    os.makedirs(trgdir)

year = args.year
month = args.month
day = args.day

logfile = os.path.join(trgdir, f"log_{year}.csv")

# Create log file with header if it doesn't exist
if not os.path.exists(logfile):
    with open(logfile, 'w', newline='') as lf:
        writer = csv.writer(lf)
        writer.writerow(["date", "area", "status"])

def log_status(date, area, status):
    with open(logfile, 'a', newline='') as lf:
        writer = csv.writer(lf)
        writer.writerow([date, area, status])

#Specify cmd path to snap gpt
cmd_path_gpt = '/Applications/esa-snap/bin/gpt'

# Identify the property file
# please check geometry, source files, and output filename
prop = f'{wkd}/props/S3_L3binning_{area}.{year}{month}{day}.properties'
templ_prop = f'{wkd}/S3_L3binning_{area}.properties'
shutil.copy(templ_prop, prop)


# Add to the prop file the listfiles and output filename
pattern = f'{srcdir}/{year}/{month}/L2_of_S3A_OL_1_EFR____{year}{month}{day}T*.SEN3.nc'
output_file = f"{trgdir}/L3_of_S3A_OL_1_EFR_{year}{month}{day}.nc"

with open(prop, 'a') as pf:
    pf.write(f'\nlistfiles={pattern}')
    pf.write(f'\noutput={output_file}')

# Check for input files
files = glob.glob(pattern)
if not files:
    print(f"⚠️ No input files found for {year}-{month}-{day} → skipping binning")
    log_status(f"{year}{month}{day}", area, "NO_INPUT_FILES")
    exit(0)

# def call_subprocess(command_string):
#     try:
#         subprocess.call(command_string)
#     except:
#         print('\nsubprocess.call() did not work.')

# import glob

# with open(prop, 'r') as pf:
#     for line in pf:
#         if line.startswith('listfiles'):
#             pattern = line.split('=')[1].strip()
#             files = glob.glob(pattern)
#             if not files:
#                 print(f"No files found for pattern: {pattern}")
#             else:
#                 for f in files:
#                     print(f"File found: {f}")


import netCDF4 as nc

# Function to check if NetCDF contains any valid (non-NaN) data
def is_empty_nc(filepath):
    try:
        with nc.Dataset(filepath, 'r') as ds:
            for var_name, var in ds.variables.items():
                # Skip purely coordinate or metadata variables
                if var.ndim == 0 or var_name.lower() in ["lat", "lon", "time"]:
                    continue
                data = var[:]
                if np.any(np.isfinite(data)):  # Found at least one real value
                    return False
        return True
    except:
        return True  # If unreadable, treat as empty

def binning(prop):
    print("\nBinning...")
    cmd = [cmd_path_gpt, xmlfile, '-e', '-p', prop]
    print("Running command:", " ".join(cmd))  # debug print
    subprocess.call(cmd)


binning(prop)

# Validate output
if os.path.exists(output_file):
    if is_empty_nc(output_file):
        print(f"⚠️ Empty output detected → deleting {output_file}")
        os.remove(output_file)
        log_status(f"{year}{month}{day}", area, "EMPTY_OUTPUT_DELETED")
    else:
        print(f"✅ Valid output kept: {output_file}")
        log_status(f"{year}{month}{day}", area, "BINNING_SUCCESS")
else:
    print("⚠️ SNAP did not produce an output file")
    log_status(f"{year}{month}{day}", area, "NO_OUTPUT_PRODUCED")


# ncf = [f for f in os.listdir(wkd) if f.endswith('.nc')]
# if ncf:
#     shutil.move(os.path.join(wkd, ncf[0]), trgdir)
