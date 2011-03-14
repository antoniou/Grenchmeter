#!/bin/bash

# we assume here that the output directory is under /tmp
# TODO: a more flexible mechanism
OUT_DIR_TMP=`echo $1 | sed 's/\/test.*//'`
OUT_DIR=`echo $OUT_DIR_TMP | sed 's/\/tmp\///'`

cd /tmp
echo "[`date`] [karajan_wrapper_remote.sh] Submitting Karajan workflow $1 ..."
#echo "[karajan_wrapper.sh] Out dir is:"
#echo $OUT_DIR
echo "[karajan_wrapper.sh] Current dir is: `pwd`"

#scp grenchmark_out.zip condor@statia1-dual.grid.pub.ro:/tmp
#ssh -x -C -q -n -o StrictHostKeyChecking=no condor@statia1-dual.grid.pub.ro "cd /tmp ; unzip grenchmark_out.zip ; mv $OUT_DIR_BKP $OUT_DIR"
#echo ${2}
#echo ${3}
#ssh -x -C -q -n -o StrictHostKeyChecking=no ${2}@${3} ". .profile && hostname ; cd /tmp ; cog-workflow $1 && echo done_workflow"
ssh -x -C -q -n -o StrictHostKeyChecking=no corina@statia1-dual.grid.pub.ro ". .profile ; cd /tmp ; cog-workflow $1 && echo workflow_done"
#DAGMAN_LOG=${1}'.dagman.log'
echo "[`date`] [karajan_wrapper_remote.sh] $1 done..."

 