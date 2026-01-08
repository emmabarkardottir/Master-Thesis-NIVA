# import relevant packages
import numpy as np
import os
from os.path import exists
import subprocess
from datetime import datetime
import shutil

# Specify scene for binning
scene = '32VNM'
selected_year = 2024
#Specify working directory and script source
wkd   = r'D:\\SATanalysis\SatelliteInLakes\\'
xmlfile = r' {}\L3binning_{}_C2RCC.xml'.format(wkd, scene)
trgdir = r'W:/Satellite/S2/L3/Marine/{}/{}/'.format(scene, selected_year)

#Specify cmd path to snap gpt
cmd_path_gpt = r'C:/Data/esa-snap/bin/gpt.exe '

# Identify the property file
# please check geometry, source files, and output filename
prop = r'{}\properties\L3binning_{}.properties'.format(wkd, scene)

def call_subprocess(command_string):
    try:
        subprocess.call(command_string)
    except:
        print('\nsubprocess.call() did not work.')

def binning(prop):
    wg = str(cmd_path_gpt + xmlfile)
    properties = prop
    cmdwget = '%s -e -p %s' %(wg, properties)
    print ("\nBinning...")   
    subprocess.call(cmdwget) 

binning(prop)

# Move output file to the target directory
ncf = [f for f in os.listdir(wkd) if '.nc' in f]
shutil.move(os.path.join(wkd+ncf[0]), trgdir)
