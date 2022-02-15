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
VRTstatistics-plot -d combined.json --predicate 'role == "receiver" and "PointCloudRenderer" in component' points_per_cloud
#
# Graph latencies
VRTstatistics-filter combined.json pointcloud_latencies.csv '("renderer_queue_ms" in record and role == "receiver") or "decoder_queue_ms" in record or "encoder_queue_ms" in record or "transmitter_queue_ms" in record or "receive_ms" in record' sessiontime downsample_ms encoder_queue_ms encoder_ms transmitter_queue_ms decoder_queue_ms decoder_ms decoded_queue_ms renderer_queue_ms latency_ms receive_ms   
VRTstatistics-plot -d combined.json --predicate '("renderer_queue_ms" in record and role == "receiver") or "decoder_queue_ms" in record or "encoder_queue_ms" in record or "transmitter_queue_ms" in record or "receive_ms" in record' downsample_ms encoder_queue_ms encoder_ms transmitter_queue_ms decoder_queue_ms decoder_ms decoded_queue_ms renderer_queue_ms latency_ms receive_ms   
#
# Graph framerates
VRTstatistics-filter combined.json pointcloud_framerates.csv '"fps" in record' sessiontime role.component=fps
VRTstatistics-plot -d combined.json --predicate '"fps" in record' role.component=fps
#
# Graph dropped framerates
VRTstatistics-filter combined.json pointcloud_droprates.csv '"fps_dropped" in record' sessiontime role.component=fps_dropped
VRTstatistics-plot -d combined.json --predicate '"fps_dropped" in record' role.component=fps_dropped
#
# Graph timestamps
VRTstatistics-filter combined.json pointcloud_timestamps.csv '"timestamp" in record and timestamp > 0' sessiontime role.component=timestamp
VRTstatistics-plot -d combined.json --predicate '"timestamp" in record and timestamp > 0' role.component=timestamp
#
# Save graphs
VRTstatistics-plot -o pointcloud_sizes.png -d pointcloud_sizes.csv
VRTstatistics-plot -o pointcloud_latencies.png -d pointcloud_latencies.csv
VRTstatistics-plot -o pointcloud_timestamps.png -d pointcloud_timestamps.csv
VRTstatistics-plot -o pointcloud_framerates.png -d pointcloud_framerates.csv
VRTstatistics-plot -o pointcloud_droprates.png -d pointcloud_droprates.csv
