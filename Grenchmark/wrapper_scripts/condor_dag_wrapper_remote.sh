#!/bin/bash

# we assume here that the output directory is under /tmp
# TODO: a more flexible mechanism
OUT_DIR_TMP=`echo $1 | sed 's/\/test.*//'`
OUT_DIR=`echo $OUT_DIR_TMP | sed 's/\/tmp\///'`

cd /tmp
echo "[condor_dag_wrapper_remote.sh] Out dir is:"
echo $OUT_DIR
echo "[condor_dag_wrapper_remote.sh] Current dir is:"
echo `pwd`
#tar czf grenchmark_out.tgz ${OUT_DIR}
#OUT_DIR_BKP=${OUT_DIR}a
#cp -r $OUT_DIR $OUT_DIR_BKP
#zip -r grenchmark_out.zip ${OUT_DIR_BKP}

#scp grenchmark_out.zip condor@statia1-dual.grid.pub.ro:/tmp
#ssh -x -C -q -n -o StrictHostKeyChecking=no condor@statia1-dual.grid.pub.ro "cd /tmp ; unzip grenchmark_out.zip ; mv $OUT_DIR_BKP $OUT_DIR"
ssh -x -C -q -n -o StrictHostKeyChecking=no corina@statia1-dual.grid.pub.ro ". ~/.bashrc ; cd /tmp ; /home/condor/condor/bin/condor_submit_dag $1"
DAGMAN_LOG=${1}'.dagman.log'
echo "[condor_wrapper] DAGMan log is:"
echo $DAGMAN_LOG
ssh -x -C -q -n -o StrictHostKeyChecking=no corina@statia1-dual.grid.pub.ro ". ~/.bashrc ; /home/condor/condor/bin/condor_wait $DAGMAN_LOG"

 