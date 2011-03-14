#!/bin/bash

# we assume here that the output directory is under /tmp
# TODO: a more flexible mechanism
#OUT_DIR_TMP=`echo $1 | sed 's/\/test.*//'`
#OUT_DIR=`echo $OUT_DIR_TMP | sed 's/\/tmp\///'`
LOG_FILE=`cat $1 | grep log | sed 's/log = //'`


#cd /tmp
echo "[condor_submit_wrapper.sh] Log file is:"
echo $LOG_FILE
echo "[condor_submit_wrapper.sh] Current dir is:"
echo `pwd`
#tar czf grenchmark_out.tgz ${OUT_DIR}
#OUT_DIR_BKP=${OUT_DIR}a
#cp -r $OUT_DIR $OUT_DIR_BKP
#zip -r grenchmark_out.zip ${OUT_DIR_BKP}

#scp grenchmark_out.zip condor@statia1-dual.grid.pub.ro:/tmp
#ssh -x -C -q -n -o StrictHostKeyChecking=no condor@statia1-dual.grid.pub.ro "cd /tmp ; unzip grenchmark_out.zip ; mv $OUT_DIR_BKP $OUT_DIR"
ssh -x -C -q -n -o StrictHostKeyChecking=no condor@statia1-dual.grid.pub.ro "echo Start_submitting; condor_submit $1; echo Done_submitting"
#DAGMAN_LOG=${1}'.dagman.log'
#echo "[condor_wrapper] DAGMan log is:"
#echo $DAGMAN_LOG
ssh -x -C -q -n -o StrictHostKeyChecking=no condor@statia1-dual.grid.pub.ro "echo Start_waiting; touch $LOG_FILE; condor_wait -debug $LOG_FILE && echo Done_waiting"

 