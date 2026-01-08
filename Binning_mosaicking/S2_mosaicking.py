import os
import sys
import os.path
from os.path import exists
from os import listdir
import subprocess
from datetime import datetime
import zipfile
import shutil
import xml.etree.ElementTree as ET
import correct_producttype

def call_subprocess(command_string):
    try:
        subprocess.call(command_string)
    except:
        print('\nsubprocess.call() did not work.')


D_work_d = r'D:\\Prosjekt\satelitt\\Kopi_import_MERIS_ftp'
d2dir = r'D:\SATanalysis\SatelliteInLakes\\'
cmd_path_acolite = r'D:\\acolite_py_win\dist\\acolite\\acolite.exe'

cmd_path_pconvert = r'C:/Data/esa-snap/bin/pconvert.exe '
cmd_path_gpt = r'C:/Data/esa-snap/bin/gpt.exe '

wkd = r'D:\\SATanalysis\SatelliteInLakes'
S2_mosaic = [r'{}\S2_mosaicking_Oslofjord_4tiles.xml'.format(wkd), 
             r'{}\S2_mosaicking_Oslofjord_3tiles.xml'.format(wkd),
             r'{}\S2_mosaicking_Oslofjord_2tiles.xml'.format(wkd)]

srcdir = r'W:\Satellite\S2\L2\Marine\Oslofjorden\c2rcc\_60m\\'
trgdir = r'W:\Satellite\S2\L2\Marine\Oslofjorden\c2rcc\_60m\Mosaic\\'

# Tiles for mosaicking
tiles = ['T32VNL', 'T32VNM', 'T32VPL', 'T32VPM'] # 4 tiles for Oslofjord (both inner and outer Oslofjord)
files = [f for f in os.listdir(srcdir) if ((tiles[0] in f) | (tiles[1] in f) | (tiles[2] in f) | (tiles[3] in f))]

dates =  []
for f in files:
    idcode = f.split("_")[2:5]
    tostring = idcode[0]+'_'+idcode[1]+'_'+idcode[2]#+'_'+idcode[3]+'_'+idcode[4]+'_'+idcode[5]
    tt = f.split("_")[7]
    dates.append(tostring)

dates = list(set(dates))

for i,dd in enumerate(dates):
    products = [f for f in os.listdir(srcdir) if (dd in f) & ((tiles[0] in f) | (tiles[1] in f) | (tiles[2] in f) | (tiles[3] in f))]
    targetname = products[0][:51]+products[0][58:73]+'_Oslofjord_mosaic.nc'
    trgfname=os.path.join(trgdir,targetname)
    inputpath = []
    for i in range(len(products)):
        inputf = os.path.join(srcdir+products[i])
        inputpath.append(inputf)
    if not exists(trgfname):
        print ('Running mosaic on '  + targetname)
        print ('Mosaicking of {} product(s)'.format(len(products)))
        if len(products) == 4:
            wg = str(cmd_path_gpt + S2_mosaic[0]) 
            cmdwget = '%s -e -Pinput1="%s" -Pinput2="%s" -Pinput3="%s" -Pinput4="%s" -Poutput="%s"' %(wg, inputpath[0], inputpath[1], inputpath[2], inputpath[3], trgfname) 
            call_subprocess(cmdwget)
        elif len(products) == 3:
            wg = str(cmd_path_gpt + S2_mosaic[1]) 
            cmdwget = '%s -e -Pinput1="%s" -Pinput2="%s" -Pinput3="%s" -Poutput="%s"' %(wg, inputpath[0], inputpath[1], inputpath[2], trgfname) 
            call_subprocess(cmdwget)
        elif len(products) == 2:
            wg = str(cmd_path_gpt + S2_mosaic[2]) 
            cmdwget = '%s -e -Pinput1="%s" -Pinput2="%s" -Poutput="%s"' %(wg, inputpath[0], inputpath[1], trgfname) 
            call_subprocess(cmdwget)
        elif len(products) == 1:
            shutil.copy2(inputpath[0], trgfname)

