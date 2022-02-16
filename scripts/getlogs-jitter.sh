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
VRTstatistics-plot -d combined.json -t "receiver point counts" --predicate '"receiver.pc.renderer" in component_role' sessiontime component_role=points_per_cloud
#
# Graph latencies
VRTstatistics-filter -d combined.json -o pointcloud_latencies.csv --predicate '".pc." in component_role' sessiontime component_role.=downsample_ms component_role.=encoder_queue_ms component_role.=encoder_ms component_role.=transmitter_queue_ms component_role.=decoder_queue_ms component_role.=decoder_ms component_role.=decoded_queue_ms component_role.=renderer_queue_ms component_role.=latency_ms component_role.=receive_ms   
VRTstatistics-plot -d combined.json -t "latency contributions" --predicate '".pc." in component_role' component_role.=downsample_ms component_role.=encoder_queue_ms component_role.=encoder_ms component_role.=transmitter_queue_ms component_role.=decoder_queue_ms component_role.=decoder_ms component_role.=decoded_queue_ms component_role.=renderer_queue_ms component_role.=latency_ms component_role.=receive_ms   
#
# Graph framerates
VRTstatistics-filter -d combined.json -o pointcloud_framerates.csv --predicate 'component_role and "fps" in record' sessiontime component_role=fps
VRTstatistics-plot -d combined.json -t "fps" --predicate 'component_role and "fps" in record' component_role=fps
#
# Graph dropped framerates
VRTstatistics-filter -d combined.json -o pointcloud_droprates.csv --predicate 'component_role and "fps_dropped" in record' sessiontime component_role=fps_dropped
VRTstatistics-plot -d combined.json -t "fps dropped" --predicate 'component_role and "fps_dropped" in record' component_role=fps_dropped
#
# Graph timestamps
VRTstatistics-filter -d combined.json -o pointcloud_timestamps.csv --predicate 'component_role and "timestamp" in record and timestamp > 0' sessiontime component_role=timestamp
VRTstatistics-plot -d combined.json -t "timestamp progression" --predicate 'component_role and "timestamp" in record and timestamp > 0' component_role=timestamp
#
# Save graphs
VRTstatistics-plot -o pointcloud_sizes.png -d pointcloud_sizes.csv
VRTstatistics-plot -o pointcloud_latencies.png -d pointcloud_latencies.csv
VRTstatistics-plot -o pointcloud_timestamps.png -d pointcloud_timestamps.csv
VRTstatistics-plot -o pointcloud_framerates.png -d pointcloud_framerates.csv
VRTstatistics-plot -o pointcloud_droprates.png -d pointcloud_droprates.csv
