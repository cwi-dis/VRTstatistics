#!/bin/bash
set -e

# Find script directory and python
scriptdir=`dirname $0`
scriptdir=`(cd $scriptdir ; pwd)`
if [ -f $scriptdir/.venv/bin/activate ]; then
	. $scriptdir/.venv/bin/activate
else
	. $scriptdir/.venv/Scripts/activate
fi
# Where the logfiles should be copied from
winPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log"
macPath="Library/Application\ Support/i2Cat/VRTogether/statistics.log"

#senderlog="vrtogether@vrtiny.local:$winPath"
#receiverlog="localhost:$macPath"
senderlog="vrtogether@scallion.local:$winPath"
receiverlog="localhost:$winPath"

set -x
# Get datafiles
scp "$senderlog" sender.log
scp "$receiverlog" receiver.log
# convert to json
python $scriptdir/stats2json.py sender.log sender.json
python $scriptdir/stats2json.py receiver.log receiver.json
# There's nothing to conbine, but we do want to fix timestamps and all that
python $scriptdir/combine.py sender.json receiver.json combined.json
# Show a graph with rendered pointcloud sizes
# This is expected to be "good enough" to judge whether we're doing the right thing.
python $scriptdir/filter.py combined.json pointcloud_sizes.csv 'role == "receiver" and "PointCloudRenderer" in component' sessiontime points_per_cloud
python $scriptdir/plot.py pointcloud_sizes.csv
#
# Graph latencies
python $scriptdir/filter.py combined.json pointcloud_latencies.csv '("renderer_queue_ms" in record and role == "receiver") or "decoder_queue_ms" in record or "encoder_queue_ms" in record or "transmitter_queue_ms" in record' sessiontime encoder_queue_ms encoder_ms transmitter_queue_ms decoder_queue_ms decoder_ms decoded_queue_ms renderer_queue_ms latency_ms     
python $scriptdir/plot.py pointcloud_latencies.csv
#
# Graph framerates
python $scriptdir/filter.py combined.json pointcloud_framerates.csv '"fps" in record' sessiontime role.component=fps
python $scriptdir/plot.py pointcloud_framerates.csv
#
# Graph dropped framerates
python $scriptdir/filter.py combined.json pointcloud_droprates.csv '"fps_dropped" in record' sessiontime role.component=fps_dropped
python $scriptdir/plot.py pointcloud_droprates.csv
#
# Graph timestamps
python $scriptdir/filter.py combined.json pointcloud_timestamps.csv '"timestamp" in record and timestamp > 0' sessiontime role.component=timestamp
python $scriptdir/plot.py pointcloud_timestamps.csv
#
# Save graphs
python $scriptdir/plot.py -o pointcloud_sizes.png pointcloud_sizes.csv
python $scriptdir/plot.py -o pointcloud_latencies.png pointcloud_latencies.csv
python $scriptdir/plot.py -o pointcloud_timestamps.png pointcloud_timestamps.csv
python $scriptdir/plot.py -o pointcloud_framerates.png pointcloud_framerates.csv
python $scriptdir/plot.py -o pointcloud_droprates.png pointcloud_droprates.csv
