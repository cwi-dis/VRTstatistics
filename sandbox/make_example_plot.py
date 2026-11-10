import sys
from VRTstatistics.datastore import DataStore
from VRTstatistics.plots import PlotStyle, render_latencies, publish_plots
from VRTstatistics.views import extract_latencies

run_dir, out_dir = sys.argv[1], sys.argv[2]
ds = DataStore(f"{run_dir}/combined.json")
ds.load()
style = PlotStyle(figsize=(10, 5), legend_kwargs=dict(ncols=2, labelspacing=0.2))
axes = render_latencies(extract_latencies(ds), style=style)
for ext in ("png", "pdf"):
    publish_plots(axes, dirname=out_dir, file_name=f"example-latencies.{ext}", format=ext, saveplot=True, showplot=False)
