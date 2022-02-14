#!/bin/bash
set -e

# Find script directory and python
scriptdir=`dirname $0`
scriptdir=`(cd $scriptdir/.. ; pwd)`
if [ -f $scriptdir/.venv/bin/activate ]; then
	. $scriptdir/.venv/bin/activate
else
	. $scriptdir/.venv/Scripts/activate
fi

sender="vrtiny.local"
receiver="sap.local"

set -x

VRTstatistics-ingest $sender $receiver

# Show a graph with rendered pointcloud sizes
# This is expected to be "good enough" to judge whether we're doing the right thing.
VRTstatistics-filter combined.json pointcloud_sizes.csv 'role == "receiver" and "PointCloudRenderer" in component' sessiontime points_per_cloud
VRTstatistics-plot pointcloud_sizes.csv
#
# Graph latencies
VRTstatistics-filter combined.json pointcloud_latencies.csv '("renderer_queue_ms" in record and role == "receiver") or "decoder_queue_ms" in record or "encoder_queue_ms" in record or "transmitter_queue_ms" in record or "receive_ms" in record' sessiontime downsample_ms encoder_queue_ms encoder_ms transmitter_queue_ms decoder_queue_ms decoder_ms decoded_queue_ms renderer_queue_ms latency_ms receive_ms   
VRTstatistics-plot pointcloud_latencies.csv
#
# Graph framerates
VRTstatistics-filter combined.json pointcloud_framerates.csv '"fps" in record' sessiontime role.component=fps
VRTstatistics-plot pointcloud_framerates.csv
#
# Graph dropped framerates
VRTstatistics-filter combined.json pointcloud_droprates.csv '"fps_dropped" in record' sessiontime role.component=fps_dropped
VRTstatistics-plot pointcloud_droprates.csv
#
# Graph timestamps
VRTstatistics-filter combined.json pointcloud_timestamps.csv '"timestamp" in record and timestamp > 0' sessiontime role.component=timestamp
VRTstatistics-plot pointcloud_timestamps.csv
#
# Save graphs
VRTstatistics-plot -o pointcloud_sizes.png pointcloud_sizes.csv
VRTstatistics-plot -o pointcloud_latencies.png pointcloud_latencies.csv
VRTstatistics-plot -o pointcloud_timestamps.png pointcloud_timestamps.csv
VRTstatistics-plot -o pointcloud_framerates.png pointcloud_framerates.csv
VRTstatistics-plot -o pointcloud_droprates.png pointcloud_droprates.csv
