#!/bin/sh

# --------------------------------------
# Log:
# 15/05/2008 C.S. 0.2	Added new parameters (and functionality) for: running locally or remotely,
#			generating a new workload or not, running a specified type of workload
# --------------------------------------

echo "[runtest.sh] Starting Grenchmark..."
echo "[runtest.sh] Arg 1: " $1
echo "[runtest.sh] Arg 2: " $2
echo "[runtest.sh] Arg 3: " $3
echo "[runtest.sh] Arg 4: " $4
echo "[runtest.sh] Arg 5: " $5
echo "[runtest.sh] Arg 6: " $6
echo "[runtest.sh] Arg 7: " $7
echo "[runtest.sh] Arg 8: " $8
echo "[runtest.sh] Arg 9: " $9
echo "[runtest.sh] Arg 10: " ${10}
echo "[runtest.sh] Arg 11: " ${11}
echo "[runtest.sh] Arg 12 (current time): " ${12}

echo "[runtest.sh] Arg 13 (R - run remote): " ${13}
echo "[runtest.sh] Arg 14 (H - remote host)): " ${14}
echo "[runtest.sh] Arg 15 (S - remote user): " ${15}
echo "[runtest.sh] Arg 16 (G - generate worload): " ${16}
echo "[runtest.sh] Arg 17 (N - workload number to test): " ${17}
echo "[runtest.sh] Arg 18 (F - output dir): " ${18}

cd grenchmark

# $1 - logfile (single/multiple)
# $2 - pushperiod (msec)
# $3 - command_line_arguments
# $4 - workload distribution
# $5 - monitoring info gathering (alwasy push ?)
# $6 - executable file name
# $7 - jobs per tester
# $8 - job type
# $9 - test id
# ${10} - tester id


LOGFILE=$1
PUSH_PERIOD=$2
CMD_LINE_ARGS=$3
WL_DISTR=$4
MON_INFO_GATH=$5
EXE_NAME=$6
NUMJOBS=$7
JOBTYPE=$8
TEST_ID=$9
PROJECT_ID=${10}
TESTER_ID=${11}
START_TIME=${12}

RUN_REMOTE="${13}"
REMOTE_HOST=${14}
REMOTE_USER=${15}
GENERATE_WL="${16}"
WL_NO=${17}
OUTDIR=${18}/gmark0${TESTER_ID}

#OUTDIR='/net/statia1-dual.grid.pub.ro/home/corina/tmp/gmark'$TESTER_ID
#OUTDIR='/tmp/gmark_'`hostname`$TESTER_ID
#OUTDIR_REL='gmark_'`hostname`${TESTER_ID}a

OUTDIR_BKP=${OUTDIR}a
echo "[runtest.sh] Output dir is: " $OUTDIR

CURRENTDIR=`pwd`
echo "[runtest.sh] Current dir is: " $CURRENTDIR

if [ $GENERATE_WL = "true" ] 
then
# generate a work-load description file
#./echo-params $TEST_ID$TESTER_ID unitary $NUMJOBS $JOBTYPE single 1 *:? $WL_DISTR "cmdline=$EXE_NAME $CMD_LINE_ARGS" >wl-desc.in
    ./echo-params $TEST_ID$TESTER_ID composite $NUMJOBS DAG -  -  - $WL_DISTR "ExternalFile=dag1.xin" >wl-desc.in

    if [ -d ./out/ ] ; then cd ./out/ ; rm -f -r * ; cd .. ; else mkdir out ; fi
    
    echo "[runtest.sh] Generating workload..."
    python wl-gen.py -d 6000000 -o $OUTDIR -j $JOBTYPE
    #python wl-gen.py -d 6000000 -o $OUTDIR -j gt4-jdf,condor-jdf
fi

cp -r $OUTDIR $OUTDIR_BKP

if [ $RUN_REMOTE = "true" ]
then
    echo "[runtest.sh] Running remotely..."    
    cd /tmp
    rm -f grenchmark_out.zip
    zip -qr grenchmark_out.zip $OUTDIR_REL
    scp grenchmark_out.zip ${REMOTE_USER}@${REMOTE_HOST}:/tmp
    ssh -x -C -q -n -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "cd /tmp ; unzip -q grenchmark_out.zip ; mv $OUTDIR_BKP $OUTDIR"
else
    echo "[runtest.sh] Running locally..."
fi    


#if [ -d ./out/run/ ] ; then cd ./out/run/ ; rm -f -r * ; cd ../.. ; else mkdir out/run ; fi

if [ -d ${OUTDIR}/run/ ] ; then cd ${OUTDIR}/run/ ; rm -f -r * ; cd ../.. ; else mkdir ${OUTDIR}/run ; fi

if [ "$LOGFILE" = "single" ] ; then ONEFILE=--onefile ; fi

export PATH=$PATH:`pwd`
#echo "Path is:"
#echo $PATH

cd $CURRENTDIR
WL_FILE='wl-to-submit.wl'$WL_NO
python wl-submit.py ${OUTDIR}/${WL_FILE} --threads=25 --nobackground $ONEFILE --testid=$TEST_ID --testerid=$TESTER_ID "--projectid=$PROJECT_ID" --starttime=$START_TIME 2>errlog.err

echo "[runtest.sh] Workload submitted..."

#cd $OUTDIR

#for JDFGEN_DIR in `find . -name "jdfs-*" | sed 's/.\///'`; do
#    for SRC_DIR in `find jdfs -name "jdf-*"`; do
#	#echo "source: " $SRC_DIR
#        DEST_DIR=`echo $SRC_DIR | sed "s/jdfs/$JDFGEN_DIR/"`
#        echo "Copying JDF dirs from " $SRC_DIR " to: " $DEST_DIR
#        cp -r $SRC_DIR/* $DEST_DIR
#    done
#done

#cd $CURRENTDIR