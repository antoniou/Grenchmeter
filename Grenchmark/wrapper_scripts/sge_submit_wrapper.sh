#!/bin/bash

# Wrapper script that submits an individual job to SGE and waits 
# for it to finish.
# Arguments:
# $1 - the job's JDF

# we assume here that the output directory is under /tmp
# TODO: a more flexible mechanism
#OUT_DIR_TMP=`echo $1 | sed 's/\/test.*//'`
#OUT_DIR=`echo $OUT_DIR_TMP | sed 's/\/tmp\///'`

source /opt/n1sge6/CorinaCluster/common/settings.sh

echo "[`date`] [sge_submit_wrapper.sh] Start submitting... " $1
/opt/n1sge6/bin/lx24-amd64/qsub -sync y $1
echo "[`date`] [sge_submit_wrapper.sh] Done job ..." $1

 