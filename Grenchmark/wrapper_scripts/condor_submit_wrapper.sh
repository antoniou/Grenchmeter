#!/bin/bash

# Wrapper script that submits an individual job to Condor and waits 
# for it to finish.
# Arguments:
# $1 - the job's JDF

# we assume here that the output directory is under /tmp
# TODO: a more flexible mechanism
#OUT_DIR_TMP=`echo $1 | sed 's/\/test.*//'`
#OUT_DIR=`echo $OUT_DIR_TMP | sed 's/\/tmp\///'`
LOG_FILE=`cat $1 | grep log | sed 's/log = //'`
echo "[condor_submit_wrapper.sh] Log file is:"
echo $LOG_FILE
#echo "[condor_submit_wrapper.sh] Current dir is:"
#echo `pwd`

echo "[`date`] [condor_submit_wrapper.sh] Start submitting..."
/home/condor/condor/bin/condor_submit $1
echo "[`date`] [condor_submit_wrapper.sh] Done submitting..."
#DAGMAN_LOG=${1}'.dagman.log'
#echo "[condor_wrapper] DAGMan log is:"
#echo $DAGMAN_LOG
touch $LOG_FILE 
/home/condor/condor/bin/condor_wait -debug $LOG_FILE && echo "[`date`] [condor_submit_wrapper.sh] Job done"

 