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
RECEIVER_SSH_ID=localhost

# Find script directory and python
scriptdir=`dirname $0`
scriptdir=`(cd $scriptdir ; pwd)`
if [ -f $scriptdir/.venv/bin/activate ]; then
	. $scriptdir/.venv/bin/activate
else
	. $scriptdir/.venv/Scripts/activate
fi
winPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log"
macPath="Library/Application\ Support/i2Cat/VRTogether/statistics.log"
set -x
# Get datafiles
scp "${SENDER_SSH_ID}:$winPath" sender.log
scp "${RECEIVER_SSH_ID}:$macPath" receiver.log
# convert to json
python $scriptdir/stats2json.py sender.log sender.json
python $scriptdir/stats2json.py receiver.log receiver.json
# There's nothing to conbine, but we do want to fix timestamps and all that
python $scriptdir/combine.py sender.json receiver.json combined.json
# Show a graph with rendered pointcloud sizes
# This is expected to be "good enough" to judge whether we're doing the right thing.
python $scriptdir/filter.py combined.json pointcloud_sizes.csv 'role == "receiver" and "PointCloudRenderer" in component' sessiontime component=points_per_cloud
python $scriptdir/plot.py pointcloud_sizes.csv
#
# Graph latencies
python $scriptdir/filter.py combined.json pointcloud_latencies.csv 'role == "receiver" and "PointCloudRenderer" in component' sessiontime component=latency_ms
python $scriptdir/plot.py pointcloud_latencies.csv
