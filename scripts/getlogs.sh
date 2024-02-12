#!/bin/bash
set -e
#
# These settings work for Jack at home, with VPN to Pampus.
# Expects a .venv python virtualenv in the scripts directory
#
# CWI
SENDER_SSH_ID=dis@fiddlehead.local
RECEIVER_SSH_ID=dis@topinambur.local
SENDER_STATS_PATH="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt"
RECEIVER_STATS_PATH="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt"
# Jack work overrides for testing
SENDER_SSH_ID=vrtogether@vrtiny.local
RECEIVER_SSH_ID=jack@flauwte.local
RECEIVER_STATS_PATH="Library/Application Support/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt"

# Find script directory and python
scriptdir=`dirname $0`
topdir=`dirname "${scriptdir}"`
topdir=`(cd "$topdir" ; pwd)`
#if [ -f $topdir/.venv/bin/activate ]; then
#	. $topdir/.venv/bin/activate
#else
#	. $topdir/.venv/Scripts/activate
#fi

set -x
# Get datafiles
scp "${SENDER_SSH_ID}:${SENDER_STATS_PATH}" sender.log
scp "${RECEIVER_SSH_ID}:${RECEIVER_STATS_PATH}" receiver.log
# convert to json
python $scriptdir/stats2json.py sender.log sender.json
python $scriptdir/stats2json.py receiver.log receiver.json
# combine
python $scriptdir/combine.py sender.json receiver.json combined.json
# Show a graph with captured pointcloud sizes and per-tile received pointcloud sizes.
# This is expected to be "good enough" to judge whether we're doing the right thing.
python $scriptdir/filter.py combined.json pointcloud_sizes.csv '("PrerecordedLiveReader" in component) or (role == "receiver" and "PointBufferRenderer" in component)' sessiontime role.component=points_per_cloud
python $scriptdir/plot.py pointcloud_sizes.csv
