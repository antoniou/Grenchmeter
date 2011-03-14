#!/bin/sh

echo "running test :)"
echo $1
echo $2
echo $3
echo $4
echo $5
echo $6
echo $7
echo $8
echo $9
echo ${10}
echo ${11}
echo ${12}

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

# generate a work-load description file
./echo-params $TEST_ID$TESTER_ID unitary $NUMJOBS $JOBTYPE single 1 *:?
$WL_DISTR "cmdline=$EXE_NAME $CMD_LINE_ARGS" >wl-desc.in

if [ -d ./out/ ] ; then cd ./out/ ; rm -f -r * ; cd .. ; else mkdir out ; fi

python wl-gen.py -j $JOBTYPE-jdf

if [ -d ./out/run/ ] ; then cd ./out/run/ ; rm -f -r * ; cd ../.. ; else
mkdir out/run ; fi

if [ "$LOGFILE" = "single" ] ; then ONEFILE=--onefile ; fi

python wl-submit.py out/wl-to-submit.wl --nobackground $ONEFILE
--testid=$TEST_ID --testerid=$TESTER_ID "--projectid=$PROJECT_ID"
--starttime=$START_TIME 2>errlog.err