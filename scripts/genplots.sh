set -x
python ../../scripts/filter.py combined.json queuesize.csv "('max_queuesize' in record or 'max_decoder_queuesize' in record) and role=='receiver'" sessiontime component=max_queuesize component=max_decoder_queuesize
python ../../scripts/filter.py combined.json latency.csv "'pc_latency_ms' in record" sessiontime role.component=pc_latency_ms
python ../../scripts/filter.py combined.json cpu_usage.csv "'cpu' in record" sessiontime role=cpu
python ../../scripts/filter.py combined.json fps.csv "role=='receiver' and 'fps' in record and ('Decoder' in component or 'Renderer' in component)" sessiontime role.component=fps fps_display
python ../../scripts/filter.py combined.json synchronizer.csv "role=='receiver' and 'Synchronizer' in component" sessiontime fps fresh_fps stale_fps holdoff_fps
python ../../scripts/plot.py -o queuesize.png queuesize.csv
python ../../scripts/plot.py -o latency.png latency.csv
python ../../scripts/plot.py -o cpu_usage.png cpu_usage.csv
python ../../scripts/plot.py -o fps.png fps.csv
python ../../scripts/plot.py -o synchronizer.png synchronizer.csv
