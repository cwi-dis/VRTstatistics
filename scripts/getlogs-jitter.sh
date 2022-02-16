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

VRTstatistics-ingest --annotator latency $sender $receiver

# Show a graph with rendered pointcloud sizes
# This is expected to be "good enough" to judge whether we're doing the right thing.
VRTstatistics-filter -d combined.json -o pointcloud_sizes.csv --predicate '"receiver.pc.renderer" in component_role' sessiontime component_role=points_per_cloud
VRTstatistics-plot -d combined.json --predicate '"receiver.pc.renderer" in component_role' sessiontime component_role=points_per_cloud
#
# Graph latencies
VRTstatistics-filter -d combined.json -o pointcloud_latencies.csv --predicate '".pc" in component_role' sessiontime downsample_ms encoder_queue_ms encoder_ms transmitter_queue_ms decoder_queue_ms decoder_ms decoded_queue_ms renderer_queue_ms latency_ms receive_ms   
VRTstatistics-plot -d combined.json --predicate '".pc." in component_role' downsample_ms encoder_queue_ms encoder_ms transmitter_queue_ms decoder_queue_ms decoder_ms decoded_queue_ms renderer_queue_ms latency_ms receive_ms   
#
# Graph framerates
VRTstatistics-filter -d combined.json -o pointcloud_framerates.csv --predicate '"fps" in record' sessiontime role.component=fps
VRTstatistics-plot -d combined.json --predicate '"fps" in record' role.component=fps
#
# Graph dropped framerates
VRTstatistics-filter -d combined.json -o pointcloud_droprates.csv --predicate '"fps_dropped" in record' sessiontime role.component=fps_dropped
VRTstatistics-plot -d combined.json --predicate '"fps_dropped" in record' role.component=fps_dropped
#
# Graph timestamps
VRTstatistics-filter -d combined.json -o pointcloud_timestamps.csv --predicate '"timestamp" in record and timestamp > 0' sessiontime role.component=timestamp
VRTstatistics-plot -d combined.json --predicate '"timestamp" in record and timestamp > 0' role.component=timestamp
#
# Save graphs
VRTstatistics-plot -o pointcloud_sizes.png -d pointcloud_sizes.csv
VRTstatistics-plot -o pointcloud_latencies.png -d pointcloud_latencies.csv
VRTstatistics-plot -o pointcloud_timestamps.png -d pointcloud_timestamps.csv
VRTstatistics-plot -o pointcloud_framerates.png -d pointcloud_framerates.csv
VRTstatistics-plot -o pointcloud_droprates.png -d pointcloud_droprates.csv
