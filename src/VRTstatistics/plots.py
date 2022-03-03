import sys
import os
from typing import Tuple
from matplotlib.axes import Axes
import pandas
import matplotlib.pyplot as pyplot
from matplotlib.backends.backend_pdf import PdfPages

from .datastore import DataStore
from .analyze import plot_simple, plot_dataframe, TileCombiner, SessionTimeFilter

def _save_multi_plot(filename):
    pp = PdfPages(filename)
    fig_nums = pyplot.get_fignums()
    figs = [pyplot.figure(n) for n in fig_nums]
    for fig in figs:
        fig.savefig(pp, format='pdf')
    pp.close()
    
def pointcounts(ds : DataStore, dirname=None, showplot=True, saveplot=False, savecsv=False) -> pyplot.Axes:
    #
    # Plot receiver point counts
    #
    dataFilter = TileCombiner("receiver.pc.renderer.*.points_per_cloud", "points per cloud", "sum", combined=True, keep=True)
    predicate='"receiver.pc.renderer" in component_role'
    fields=['sessiontime', 'component_role.=points_per_cloud']
 
    ax = plot_simple(ds,
        noshow=True, 
        title="Receiver point counts", 
        predicate=predicate, 
        fields=fields,
        datafilter=dataFilter
        )
    bot, top = ax.get_ylim()
    ax.set_ylim(0, top*1.5)
    if saveplot:
        _save_multi_plot(os.path.join(dirname, "pointcounts.pdf"))
    if showplot:
        pyplot.show()
    if savecsv:
        #
        # Save point counts to file (including non-aggregated)
        #
        dataFilter.keep = True
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        df = dataFilter(df)
        df.to_csv(os.path.join(dirname, "pointcounts.csv"))
    return ax
    
def resource_cpu(ds : DataStore) -> pyplot.Axes:
    dataFilter=SessionTimeFilter()
    predicate='component == "ResourceConsumption"'
    ax1 = plot_simple(ds, 
        noshow=True, 
        title="CPU usage", 
        predicate=predicate, 
        fields=[
            'role.=cpu'
            ],
        datafilter=dataFilter
        )
    bot, top = ax1.get_ylim()
    ax1.set_ylim(0, top*1.5)
    return ax1

def resource_mem(ds : DataStore) -> pyplot.Axes:
    dataFilter=SessionTimeFilter()
    predicate='component == "ResourceConsumption"'
    ax2 = plot_simple(ds, 
        noshow=True, 
        title="Memory usage", 
        predicate=predicate, 
        fields=[
            'role.=mem'
            ],
        datafilter=dataFilter
        )
    bot, top = ax2.get_ylim()
    ax2.set_ylim(0, top*1.5)
    return ax2

def resource_bandwidth(ds : DataStore) -> pyplot.Axes:
    dataFilter=SessionTimeFilter()
    predicate='component == "ResourceConsumption"'
    ax3 = plot_simple(ds, 
        noshow=True, 
        title="Bandwidth usage", 
        predicate=predicate, 
        fields=[
            'role.=recv_bandwidth',
            'role.=sent_bandwidth'
            ],
        datafilter=dataFilter
        )
    bot, top = ax3.get_ylim()
    ax3.set_ylim(0, top*1.5)
    return ax3

def resources(ds : DataStore, dirname=None, showplot=True, saveplot=False, savecsv=False) -> Tuple[pyplot.Axes, pyplot.Axes, pyplot.Axes]:
    ax1 = resource_cpu(ds)
    ax2 = resource_mem(ds)
    ax3 = resource_bandwidth(ds)

    if saveplot:
        _save_multi_plot(os.path.join(dirname, "resources.pdf"))
    if showplot:
        pyplot.show()

    if savecsv:
        dataFilter=SessionTimeFilter()
        predicate='component == "ResourceConsumption"'
        df = ds.get_dataframe(predicate=predicate, fields=['sessiontime', 'role.=cpu', 'role.=mem', 'role.=recv_bandwidth', 'role.=sent_bandwidth' ])
        df = dataFilter(df)
        df.to_csv(os.path.join(dirname, "resources.csv"))
    return ax1, ax2, ax3
    
def _plot_latencies_per_tile(df : pandas.DataFrame, tilenum, ax) -> pyplot.Axes:
    fields = [
        "sender.pc.grabber.downsample_ms",
        "sender.pc.grabber.encoder_queue_ms",
        "sender.pc.encoder.encoder_ms",
        "sender.pc.encoder.transmitter_queue_ms",
        f"receiver.pc.reader.{tilenum}.receive_ms",
        f"receiver.pc.decoder.{tilenum}.decoder_queue_ms",
        f"receiver.pc.decoder.{tilenum}.decoder_ms",
        f"receiver.pc.renderer.{tilenum}.renderer_queue_ms"
    ]
    todelete = []
    for i in range(len(fields)):
        if not fields[i] in df.columns:
            alt = fields[i].replace(f'.{tilenum}.', '.all.')
            if alt in df.columns:
                fields[i] = alt
            else:
                print(f'Warning: missing field {fields[i]} in dataframe')
                todelete.append(fields[i])
    for f in todelete:
        fields.remove(f)
    latency_fields = [
        "receiver.synchronizer.latency_ms",
        f"receiver.pc.renderer.{tilenum}.latency_ms",
        f"receiver.pc.renderer.{tilenum}.latency_max_ms",
        ]
    ax = df.interpolate(method='pad').plot(x="sessiontime", y=fields, kind="area", colormap="Paired", ax=ax, legend=False)
    df.interpolate(method='pad').plot(x="sessiontime", y=latency_fields, ax=ax, color=["blue", "red", "yellow"], legend=False)
    ax.set_title(f"Per-tile Latency contributions, tile={tilenum}")
    return ax
 
def latencies_per_tile(ds : DataStore, dirname=None, showplot=True, saveplot=False) -> pyplot.Axes:
    # Per-tile
    nTiles = ds.annotator.nTiles
    if nTiles > 1:
        predicate='".pc." in component_role or component_role == "receiver.voice.renderer" or component_role == "receiver.synchronizer"'
        fields=[
            'sessiontime',
            'component_role.=downsample_ms',
            'component_role.=encoder_queue_ms',
            'component_role.=encoder_ms',
            'component_role.=transmitter_queue_ms',
            'component_role.=receive_ms',
            'component_role.=decoder_queue_ms',
            'component_role.=decoder_ms',
            'component_role.=renderer_queue_ms',
            'component_role.=latency_ms',
            'component_role.=latency_max_ms',
            ]
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        n = ds.annotator.nTiles
        ax = None
        fig, axs = pyplot.subplots(nTiles, 1, sharex=True, sharey=True)
        fig.set_figheight(fig.get_figheight()*(nTiles-1))
        fig.set_figwidth(fig.get_figwidth()*1.5)
        for i in range(nTiles):
            _plot_latencies_per_tile(df, i, axs[i])
        handles, labels = axs[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='center right')
        pyplot.subplots_adjust(right=0.66)
        if saveplot:
            _save_multi_plot(os.path.join(dirname, "latencies-per-tile.pdf"))
        if showplot:
            pyplot.show()
        return ax
   
def latencies(ds : DataStore, dirname=None, showplot=True, saveplot=False, savecsv=False) -> pyplot.Axes:
    dataFilter = (
        TileCombiner("sender.pc.grabber.downsample_ms", "downsample", "mean", combined=True) +
        TileCombiner("sender.pc.grabber.encoder_queue_ms", "encoder queue", "mean", combined=True) +
        TileCombiner("sender.pc.encoder.encoder_ms", "encoder", "mean", combined=True) +
        TileCombiner("sender.pc.encoder.transmitter_queue_ms", "transmitter queue", "mean", combined=True) +
        TileCombiner("receiver.pc.reader.*.receive_ms", "receivers", "mean", combined=True) +
        TileCombiner("receiver.pc.decoder.*.decoder_queue_ms", "decoder queues", "mean", combined=True) +
        TileCombiner("receiver.pc.decoder.*.decoder_ms", "decoders", "max", combined=True) +
        TileCombiner("receiver.pc.renderer.*.renderer_queue_ms", "renderers", "mean", combined=True)
        )
        
    #fig = pyplot.figure()
    ax = plot_simple(ds, 
        noshow=True,
        title="Latency contributions (ms)", 
        predicate='".pc." in component_role or component_role == "receiver.voice.renderer"', 
        fields=[
            'component_role.=downsample_ms',
            'component_role.=encoder_queue_ms',
            'component_role.=encoder_ms',
            'component_role.=transmitter_queue_ms',
            'component_role.=receive_ms',
            'component_role.=decoder_queue_ms',
            'component_role.=decoder_ms',
            'component_role.=renderer_queue_ms'
            ],
        datafilter = dataFilter,
        plotargs=dict(kind="area", colormap="Paired")
        )
    df = ds.get_dataframe(
        predicate='"receiver.pc.renderer" in component_role or "receiver.synchronizer" in component_role', 
        fields=[
            'sessiontime',
            'component_role.=latency_ms',
            'component_role.=latency_max_ms',
            ],
        )
    dataFilter2 = (
        TileCombiner("receiver.synchronizer.latency_ms", "synchronizer latency", "max", combined=True) +
        TileCombiner("receiver.pc.renderer.*.latency_ms", "renderer latency", "min", combined=True) +
        TileCombiner("receiver.pc.renderer.*.latency_max_ms", "max renderer latency", "max", combined=True)
        )
    df = dataFilter2(df)
    df.interpolate().plot(x="sessiontime", y=["synchronizer latency", "renderer latency", "max renderer latency"], ax=ax, color=["blue", "red", "yellow"])
    # Limit Y axis to reasonable values
    avg_latency = df["renderer latency"].mean()
    avg_max_latency = df["max renderer latency"].mean()
    avg_sync_latency = df["synchronizer latency"].mean()
    avg_latency = max(avg_latency, avg_max_latency, avg_sync_latency)
    ax.set_ylim(0, avg_latency*2)
    ax.legend(loc='upper left', fontsize='small')
    if saveplot:
        _save_multi_plot(os.path.join(dirname, "latencies.pdf"))
    if showplot:
        pyplot.show()
        
    #
    # Save to csv file, in raw form
    #
    if savecsv:
        predicate='".pc." in component_role or component_role == "receiver.voice.renderer"'
        fields=[
            'sessiontime',
            'component_role.=downsample_ms',
            'component_role.=encoder_queue_ms',
            'component_role.=encoder_ms',
            'component_role.=transmitter_queue_ms',
            'component_role.=receive_ms',
            'component_role.=decoder_queue_ms',
            'component_role.=decoder_ms',
            'component_role.=renderer_queue_ms',
            'component_role.=latency_ms'
            ]
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        df.to_csv(os.path.join(dirname, "latencies.csv"))    
    return ax

def framerates(ds : DataStore) -> pyplot.Axes:
    df = ds.get_dataframe(
        predicate='component_role and "fps" in record', 
        fields=['sessiontime', 'component_role.=fps'],
        )
    dataFilter = (
        TileCombiner("sender.voice.grabber.fps", "voice capturer", "min", combined=True, optional=True) +
        TileCombiner("sender.voice.encoder.fps", "voice encoder", "min", combined=True, optional=True) +
        TileCombiner("sender.voice.writer.fps", "voice transmitter", "min", combined=True, optional=True) +
        TileCombiner("receiver.voice.reader.fps", "voice receiver", "min", combined=True, optional=True) +
        TileCombiner("receiver.voice.preparer.fps", "voice preparer", "min", combined=True, optional=True) +
        TileCombiner("sender.pc.grabber.fps", "capturer", "min", combined=True) +
        TileCombiner("sender.pc.encoder.fps", "encoders", "min", combined=True) +
        TileCombiner("sender.pc.writer.*.fps", "transmitters", "min", combined=True) +
        TileCombiner("receiver.pc.reader.*.fps", "receivers", "min", combined=True) +
        TileCombiner("receiver.pc.decoder.*.fps", "decoders", "min", combined=True) +
        TileCombiner("receiver.synchronizer.fps", "synchronizer", "min", combined=True) +
        TileCombiner("receiver.pc.preparer.*.fps", "preparers", "min", combined=True) +
        TileCombiner("receiver.pc.renderer.*.fps", "renderers", "min", combined=True)
        )
    df = dataFilter(df)
    ax1 = plot_dataframe(df, 
        noshow=True,
        title="Frames per second", 
        x="sessiontime",
        descr=ds.annotator.description()
        )
    return ax1

def framerates_dropped(ds : DataStore) -> pyplot.Axes:
   #fig = pyplot.figure()
    dataFilter = (
        TileCombiner("sender.voice.grabber.fps_dropped", "voice capturer dropped", "min", combined=True, optional=True) +
        TileCombiner("sender.voice.encoder.fps_dropped", "voice encoder dropped", "min", combined=True, optional=True) +
        TileCombiner("receiver.voice.reader.fps_dropped", "voice receiver dropped", "min", combined=True, optional=True) +
        TileCombiner("receiver.voice.preparer.fps_dropped", "voice preparer dropped", "min", combined=True, optional=True) +

        TileCombiner("sender.pc.grabber.fps_dropped", "capturer dropped", "sum", combined=True) +
        TileCombiner("sender.pc.encoder.fps_dropped", "encoders dropped", "sum", combined=True) +
        TileCombiner("receiver.pc.reader.*.fps_dropped", "receivers dropped", "sum", combined=True) +
        TileCombiner("receiver.pc.decoder.*.fps_dropped", "decoders dropped", "sum", combined=True) +
        TileCombiner("receiver.pc.preparer.*.fps_dropped", "preparers dropped", "sum", combined=True)
        )
    ax2 = plot_simple(ds, 
        noshow=True,
        title="FPS dropped", 
        predicate='component_role and "fps_dropped" in record', 
        fields=['component_role.=fps_dropped'],
        datafilter=dataFilter
        )
    return ax2

def framerates_and_dropped(ds : DataStore, dirname=None, showplot=True, saveplot=False, savecsv=False) -> Tuple[pyplot.Axes, pyplot.Axes]:
    #fig = pyplot.figure()
    ax1 = framerates(ds)
    ax2 = framerates_dropped(ds)

    if saveplot:
        _save_multi_plot(os.path.join(dirname, "framerates.pdf"))
    if showplot:
        pyplot.show()
    #
    # Save to csv file, without combining
    #
    if savecsv:
        predicate='component_role and "fps" in record'
        fields=['sessiontime', 'component_role.=fps', 'component_role.=fps_dropped']
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        df.to_csv(os.path.join(dirname, "framerates.csv"))    
    return ax1, ax2
    
def progress(ds : DataStore, dirname=None, showplot=True, saveplot=False, savecsv=False) -> pyplot.Axes:
    df = ds.get_dataframe(
        predicate='"aggregate_packets" in record and component_role',
        fields = ['sessiontime', 'component_role=aggregate_packets']
        )
    columns = list(df.keys())
    columns.sort()
    columns.remove('sessiontime')
    columns.remove('sender.pc.grabber') # It can drop frames without being a problem.
    marker=None
    colors=["red", "blue", "green", "purple"]
    ax=None
    for y in columns:
        color='black'
        marker=None
        markevery = 100
        if '.0' in y:
            color='red'
            markevery=(20,100)
        elif '.1' in y:
            color='blue'
            markevery=(40,100)
        elif '.2' in y:
            color='green'
            markevery=(60,100)
        elif '.3' in y:
            color='purple'
            markevery=(80,100)
        if '.encoder' in y:
            marker = '*'
        elif '.writer' in y:
            marker = '>'
        elif '.decoder' in y:
            marker = 'o'
        elif '.preparer' in y:
            marker = '<'
        elif '.reader' in y:
            marker = '+'
        series = df.loc[:, ["sessiontime", y]]
        # Some columns need to be adjusted
        if ds.annotator.nTiles > 1:
            if '.all' in y:
                series[y] = series[y] / ds.annotator.nTiles
            elif y == "sender.pc.encoder":
                series[y] = series[y] / (ds.annotator.nTiles*ds.annotator.nQualities)
        ax = series.interpolate(method='pad').plot(x="sessiontime", marker=marker, markevery=markevery, color=color, alpha=0.5, ax=ax)
    ax.legend(loc='upper left', fontsize='small')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    descr = ds.annotator.description()
    ax.text(0.98, 0.98, descr, transform=ax.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props)
    ax.set_title("Pointcloud Progress")
    if saveplot:
        _save_multi_plot(os.path.join(dirname, "progress.pdf"))
    if showplot:
        pyplot.show()
    return ax
