#!/bin/bash -fvx
# zip restart files?
ZIPRES=1 

# remove log files? 
RMLOGS=0

# Set script name
sn=noresm2netcdf4

# archive path of case
ABASE=$1

if [ ! -d $ABASE ]; then
  echo "${sn}: ${ABASE} is not a directory." >&2
  exit 1
fi
cd $ABASE

# Set arguments
nthreads=4

# Set various variables
ncdump=`which ncdump`
nccopy=`which nccopy`
complevel=5 # 1-9
lid="`date +%y%m%d-%H%M%S`"

# Functions 

convert_cmd () {
  echo convert $ncfile
  rm -f ${ncfile}_tmp
  $nccopy -k 4 -s -d $complevel $ncfile ${ncfile}_tmp
  mv ${ncfile}_tmp ${ncfile}
  chmod go+r ${ncfile}
}

compress_cmd () {
  if [ $ZIPRES -eq 1 ] ; then 
    echo zip $ncfile
    gzip $ncfile
    chmod go+r ${ncfile}.gz
  fi
}

convert_loop () {

  # loop over cases 
  for ncfile in `find . -wholename '*/hist/*.nc' -print`; do
    if [[ "`$ncdump -k $ncfile`" != 'netCDF-4' && "`$ncdump -k $ncfile`" != 'netCDF-4 classic model' ]] ; then
      while :; do
        if [ `jobs -p|wc -l` -lt $nthreads ]; then
          convert_cmd &
          break
        fi
        sleep 0.1s
      done
    fi
  done
  for ncfile in `find . -wholename '*/rest/*.nc' -print`; do
      while :; do
        if [ `jobs -p|wc -l` -lt $nthreads ]; then
          compress_cmd & 
          break
        fi
        sleep 0.1s
      done
  done
  for logfile in `find . -wholename '*/logs/*' -print`; do
      if [ $RMLOGS -eq 1 ] ; then 
        rm -f $logfile
      fi
  done

  wait
  echo "${sn}: conversion completed."
}

# Execute the convert loop as a backgroud process
echo `date` > $ABASE/archive.log.$lid
convert_loop >> $ABASE/archive.log.$lid 
echo `date` >> $ABASE/archive.log.$lid
