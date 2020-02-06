#!/bin/bash
set -e

sn=`basename $0`
export DOUT_L_HOSTNAME=`./xmlquery DOUT_L_HOSTNAME --value`
export DOUT_L_ROOT=`./xmlquery DOUT_L_ROOT --value`
export DOUT_S_ROOT=`./xmlquery DOUT_S_ROOT --value`
export CASE=`./xmlquery CASE --value`
export CASEROOT=`./xmlquery CASEROOT --value`
#echo $DOUT_L_HOSTNAME
#echo $DOUT_L_ROOT
#echo $DOUT_S_ROOT
#echo $CASEROOT
#echo $USER
#-----------------------------------------------------------------------
# Create remote archive root directory.
#-----------------------------------------------------------------------

ssh $USER@$DOUT_L_HOSTNAME "mkdir -p $DOUT_L_ROOT"
#-----------------------------------------------------------------------
# Archive model output
#-----------------------------------------------------------------------
export LID="`date +%y%m%d-%H%M%S`"
echo "$sn: Archive model output and restart files..."
  rsync -avh --progress $DOUT_S_ROOT $USER@$DOUT_L_HOSTNAME:$DOUT_L_ROOT &> $DOUT_S_ROOT/../$CASE.la.log.$LID &

echo "$sn: Archiving model output completed."
echo "$sn: Archiving CASE directory..."
  rsync -avh --progress $CASEROOT/ $USER@$DOUT_L_HOSTNAME:$DOUT_L_ROOT/$CASE/case &>> $DOUT_S_ROOT/../$CASE.la.log.$LID &
echo "$sn: Archiving CASE completed."
exit 0
