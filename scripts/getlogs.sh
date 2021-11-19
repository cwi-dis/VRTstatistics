#!/bin/bash
set -e
#
# These settings work for Jack at home, with VPN to Pampus.
# Expects a .venv python virtualenv in the scripts directory
#
# CWI
#SENDER_SSH_ID=vrtogether@vrbig.local
#SENDER_SSH_ID=vr-together@vrsmall.local
#RECEIVER_SSH_ID=vrtogether@scallion.local
# Jack home
SENDER_SSH_ID=vrtogether@vrtiny.local
RECEIVER_SSH_ID=dis@valkenburg-win10.local

# Find script directory and python
scriptdir=`dirname $0`
scriptdir=`(cd $scriptdir ; pwd)`
#if [ -f $scriptdir/.venv/bin/activate ]; then
#	. $scriptdir/.venv/bin/activate
#else
#	. $scriptdir/.venv/Scripts/activate
#fi

set -x
# Get datafiles
scp ${SENDER_SSH_ID}:AppData/LocalLow/i2Cat/VRTogether/statistics.log sender.log
scp ${RECEIVER_SSH_ID}:AppData/LocalLow/i2Cat/VRTogether/statistics.log receiver.log
# convert to json
python $scriptdir/stats2json.py sender.log sender.json
python $scriptdir/stats2json.py receiver.log receiver.json
# combine
python $scriptdir/combine.py sender.json receiver.json combined.json
# Show a graph with captured pointcloud sizes and per-tile received pointcloud sizes.
# This is expected to be "good enough" to judge whether we're doing the right thing.
python $scriptdir/filter.py combined.json pointcloud_sizes.csv '("PrerecordedLiveReader" in component) or (role == "receiver" and "PointBufferRenderer" in component)' sessiontime role.component=points_per_cloud
python $scriptdir/plot.py pointcloud_sizes.csv
