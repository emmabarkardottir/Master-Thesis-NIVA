: 
datafile=$1
while read year month day; do
 echo $year $month $day
    python3 Binning_S3.py --wkd . --srcdir /Volumes/Untitled/OLCI/Bergen/L2 --trgdir /Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/L3 --area Sognefjorden --year $year --month $month --day $day
done < $datafile 