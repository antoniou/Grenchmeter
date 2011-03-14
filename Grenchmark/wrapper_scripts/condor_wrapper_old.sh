#!/bin/bash

# we assume here that the output directory is under /tmp
# TODO: a more flexible mechanism
OUT_DIR_TMP=`echo $1 | sed 's/\/test.*//'`
OUT_DIR=`echo $OUT_DIR_TMP | sed 's/\/tmp\///'`

cd /tmp
echo $OUT_DIR
echo `pwd`
tar czf grenchmark_out.tgz ${OUT_DIR}

scp grenchmark_out.tgz corina@rudolf2.grid.pub.ro:/tmp
ssh -x -C -q -n -o StrictHostKeyChecking=no corina@rudolf2.grid.pub.ro "cd /tmp ; tar zxf grenchmark_out.tgz"
ssh -x -C -q -n -o StrictHostKeyChecking=no corina@rudolf2.grid.pub.ro "cd /tmp ; condor_submit_dag $1"
 