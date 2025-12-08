import os
from typing import Tuple, Optional, List, Dict, Any, cast, Literal
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as pyplot
from matplotlib.backends.backend_pdf import PdfPages

from .datastore import DataStore, DataStoreError, Predicate
from .analyze import DataFrameFilter, TileCombiner, SessionTimeFilter, dataframe_to_pcindex_latencies_for_tile

__all__ = [
    "plot_simple", 
    "_plot_dataframe", 
    "plot_pointcounts", 
    "plot_framerates_and_dropped", 
    "plot_framerates_dropped", 
    "plot_framerates", 
    "plot_progress", 
    "plot_resources", 
    "plot_resource_cpu", 
    "plot_resource_mem", 
    "plot_resource_bandwidth", 
    "plot_latencies", 
    "plot_latencies_for_tile", 
    "plot_latencies_per_tile", 
    ]

def plot_simple(datastore : DataStore, *, predicate : Optional[Predicate]=None, title : Optional[str]=None, noshow : bool=False, x : str="sessiontime", fields : List[str]=[], datafilter : Optional[DataFrameFilter]=None, plotargs : Dict[str, Any]={}, show_desc : bool=True) -> Axes:
    """
    Plot data (optionally after converting to pandas.DataFrame).
    output is optional output file (default: show in a window)
    x is name of x-axis field
    fields is list of fields to plot (default: all, except x)
    """
    fields_to_retrieve : Optional[List[str]]= list(fields)
    fields_to_plot = fields
    # If we have specified fields to retrieve ensure our x-axis is in the list
    if fields_to_retrieve and x and not x in fields_to_retrieve:
        fields_to_retrieve.append(x)
    fields_to_plot = None # For simple plots we use all fields (except x, which is automatically ignored)
    if not fields_to_retrieve:
        fields_to_retrieve = None
    dataframe = datastore.get_dataframe(predicate=predicate, fields=fields_to_retrieve)
    if datafilter:
        dataframe = datafilter(dataframe)
    descr=None
    if show_desc:
        descr = datastore.annotator.description()
    ax1 = _plot_dataframe(dataframe, title=title, noshow=noshow, x=x, fields=fields_to_plot, descr=descr, plotargs=plotargs)
    return ax1

def _plot_dataframe(dataframe : pd.DataFrame, *, title : Optional[str]=None, noshow : bool=False, x : Any=None, fields : Optional[List[str]]=None, descr : Optional[str]=None, plotargs : Dict[str, Any]={}, interpolate : str='linear') -> Axes:
    """
    Convenience method: plot a pandas DataFrame.

    The plot is returned (as an Axes) but it is also the pyplot default current plot, so it is easy to save it after this call.
    
    :param dataframe: the dataframe to plot
    :type dataframe: pd.DataFrame
    :param title: Optional title for the plot
    :type title: Optional[str]
    :param noshow: By default plot is shown on-screen, set to true to not do so.
    :type noshow: bool
    :param x: x-axis column. Default supplied by DataFrame
    :type x: Any
    :param fields: Column names to plot.
    :type fields: Optional[List[str]]
    :param descr: Description to show on the plot
    :type descr: Optional[str]
    :param plotargs: Extra arguments to plot()
    :type plotargs: Dict[str, Any]
    :param interpolate: Method used to interpolate() the dataframe
    :type interpolate: str
    :return: the plot Axes object
    :rtype: Axes
    """
    if dataframe.empty:
        raise DataStoreError("dataframe is empty, nothing to plot")
    df_tmp = dataframe.interpolate(method=interpolate) # type: ignore
    if fields:
        plot : Axes = cast(Axes, df_tmp.plot(x=x, y=fields, **plotargs))
    else:
        plot : Axes = cast(Axes, df_tmp.plot(x=x, **plotargs))
    assert plot
    if descr:
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        plot.text(0.98, 0.98, descr, transform=plot.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props) # type: ignore
    if title:
        pyplot.title(title) # type: ignore
    plot.legend(loc='upper left', fontsize='small') # type: ignore
    if not noshow:
        pyplot.show() # type: ignore
    return plot

def _save_multi_plot(filename : str, dpi : float|Literal["figure"]="figure", format : str="pdf") -> None:
    """
    Convenience method: save the current pyplot figures as a multipage PDF or other file.
    
    :param filename: Filename to save to
    :type filename: str
    :param dpi: Description
    :type dpi: Any
    :param format: Description
    :type format: str
    """
    if format=="pdf":
        pp = PdfPages(filename)
        fig_nums = pyplot.get_fignums()
        figs = [pyplot.figure(n) for n in fig_nums] # type: ignore
        for fig in figs:
            fig.savefig(pp, bbox_inches='tight', format="pdf", pad_inches=0.05) # type: ignore
        pp.close()
    else:
        fig_nums = pyplot.get_fignums()
        figs = [pyplot.figure(n) for n in fig_nums] # type: ignore
        for fig in figs:
            fig.savefig(filename, bbox_inches='tight', dpi=dpi, format=format, pad_inches=0.01) # type: ignore
    
def plot_pointcounts(ds : DataStore, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False, savecsv : bool=False) -> Axes:
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
    _, top = ax.get_ylim()
    ax.set_ylim(0, top*1.5)
    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, "pointcounts.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    if savecsv:
        assert dirname
        #
        # Save point counts to file (including non-aggregated)
        #
        dataFilter.keep = True
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        df = dataFilter(df)
        df.to_csv(os.path.join(dirname, "pointcounts.csv"))
    return ax
    
def plot_resource_cpu(ds : DataStore) -> Axes:
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
    _, top = ax1.get_ylim()
    ax1.set_ylim(0, top*1.5)
    return ax1

def plot_resource_mem(ds : DataStore) -> Axes:
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
    _, top = ax2.get_ylim()
    ax2.set_ylim(0, top*1.5)
    return ax2

def plot_resource_bandwidth(ds : DataStore) -> Axes:
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
    _, top = ax3.get_ylim()
    ax3.set_ylim(0, top*1.5)
    return ax3

def plot_resources(ds : DataStore, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False, savecsv : bool=False) -> Tuple[Axes, Axes, Axes]:
    ax1 = plot_resource_cpu(ds)
    ax2 = plot_resource_mem(ds)
    ax3 = plot_resource_bandwidth(ds)

    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, "resources.pdf"))
    if showplot:
        pyplot.show() # type: ignore

    if savecsv:
        assert dirname
        dataFilter=SessionTimeFilter()
        predicate='component == "ResourceConsumption"'
        df = ds.get_dataframe(predicate=predicate, fields=['sessiontime', 'role.=cpu', 'role.=mem', 'role.=recv_bandwidth', 'role.=sent_bandwidth' ])
        df = dataFilter(df)
        df.to_csv(os.path.join(dirname, "resources.csv"))
    return ax1, ax2, ax3
    
def plot_latencies_for_tile(df : pd.DataFrame, tilenum : int, ax : Axes) -> Axes:
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
    todelete : List[str] = []
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
    ax.set_title(f"Per-tile Latency contributions, tile={tilenum}") # type: ignore
    return ax
 
def plot_latencies_per_tile(ds : DataStore, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False) -> Axes:
    # Per-tile
    nTiles = ds.annotator.nTiles
    assert nTiles > 1
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
    ax = None
    fig : Figure
    axs : List[Axes]
    fig, axs = pyplot.subplots(nTiles, 1, sharex=True, sharey=True) # type: ignore
    fig.set_figheight(fig.get_figheight()*(nTiles-1))
    fig.set_figwidth(fig.get_figwidth()*1.5)
    for i in range(nTiles):
        plot_latencies_for_tile(df, i, axs[i])
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right') # type: ignore
    pyplot.subplots_adjust(right=0.66)
    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, "latencies-per-tile.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax
   
def plot_latencies(ds : DataStore, dpi : float|Literal["figure"]="figure", format : str="pdf", file_name : str="latencies.pdf", title : str="Latency contributions (ms)", label_dict : Dict[str, Any]={}, tick_dict : Dict[str, Any]={}, legend_dict : Dict[str, Any]={}, labelspacing : float=0.5, ncols : int=1, use_row_major : bool=False, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False, savecsv : bool=False, max_y : float=0, show_sync : bool=True, show_desc : bool=True, figsize : Tuple[int, int]=(6, 4), show_legend : bool=True, plotargs : Dict[str, Any]={}) -> Axes:
    """
    Plot latency contributions over time.

    Some fields (such as queue durations) are plotted as a stacked area graph.
    Some other fields (like eventual end-to-end latency) are plotted as a line graph.
    
    :param ds: DataStore to plot
    :type ds: DataStore
    :param dpi: See pyplot
    :type dpi: float | Literal["figure"]
    :param format: Output file format.
    :type format: str
    :param file_name: Output file name.
    :type file_name: str
    :param title: Optional title for the plot.
    :type title: str
    :param label_dict: Extra argument to pyplot.xlabel() and ylabel()
    :type label_dict: Dict[str, Any]
    :param tick_dict: Extra arguments to pyplot.xticks() and yticks()
    :type tick_dict: Dict[str, Any]
    :param legend_dict: FontProperties prop argument to pyplot.legend()
    :type legend_dict: Dict[str, Any]
    :param labelspacing: labelspacing argument to pyplot.legend()
    :type labelspacing: float
    :param ncols: ncols argument to pyplot.legend()
    :type ncols: int
    :param use_row_major: If ncols > 1 use row-major ordering in stead of column-major ordering for legend.
    :type use_row_major: bool
    :param dirname: Name of directory where plots and CSV files are saved
    :type dirname: Optional[str]
    :param showplot: If true also show the plot on-screen
    :type showplot: bool
    :param saveplot: If true also save the plot
    :type saveplot: bool
    :param savecsv: If true also save the CSV file
    :type savecsv: bool
    :param max_y: If specified: gives maximum y. Default is to compute a reasonable value.
    :type max_y: float
    :param show_desc: Don't remember
    :type show_desc: bool
    :param figsize: Description
    :type figsize: Tuple[int, int]
    :param show_legend: Description
    :type show_legend: bool
    :param plotargs: Description
    :type plotargs: Dict[str, Any]
    :return: Description
    :rtype: Axes
    """
    #
    # Step 1 - Plot the area plot that shows things like queue durations and encoder durations.
    # These are plotted straight from the DataStore.
    #
    dataFilter = (
        # removed by Gent: TileCombiner("sender.pc.grabber.downsample_ms", "downsample", "mean", combined=True) +
        TileCombiner("sender.pc.grabber.encoder_queue_ms", "encoder queue", "mean", combined=True) +
        TileCombiner("sender.pc.encoder.encoder_ms", "encoder", "mean", combined=True) +
        TileCombiner("sender.pc.encoder.transmitter_queue_ms", "transmitter queue", "mean", combined=True) +
        # removed by Gent: TileCombiner("receiver.pc.reader.*.receive_ms", "receivers", "mean", combined=True) +
        TileCombiner("receiver.pc.decoder.*.decoder_queue_ms", "decoder queues", "mean", combined=True) +
        TileCombiner("receiver.pc.decoder.*.decoder_ms", "decoders", "max", combined=True) +
        TileCombiner("receiver.pc.renderer.*.renderer_queue_ms", "renderer queues", "mean", combined=True)
        )
        
    
    ax = plot_simple(ds, 
        noshow=True,
        title=title, 
        predicate='"sender.pc.grabber" in component_role or "sender.pc.encoder" in component_role or "receiver.pc.decoder" in component_role or "receiver.pc.renderer" in component_role or component_role == "receiver.voice.renderer"', 
        # xxxjack was: predicate='".pc." in component_role or component_role == "receiver.voice.renderer"', 
        
        fields=[
            # removed by Gent: 'component_role.=downsample_ms',
            'component_role.=encoder_queue_ms',
            'component_role.=encoder_ms',
            'component_role.=transmitter_queue_ms',
            # removed by Gent: 'component_role.=receive_ms',
            'component_role.=decoder_queue_ms',
            'component_role.=decoder_ms',
            'component_role.=renderer_queue_ms'
            ],
        datafilter = dataFilter,
        plotargs=dict(kind="area", colormap="Paired", figsize=figsize) | plotargs,
        show_desc=show_desc
        )
    #
    # Step 2 - plot some end-to-end latencies as line graphs.
    #
    dataframe_end2end_latencies = ds.get_dataframe(
        predicate='"receiver.pc.renderer" in component_role or "receiver.synchronizer" in component_role', 
        fields=[
            'sessiontime',
            'component_role.=latency_ms',
            'component_role.=latency_max_ms',
            ],
        )
    dataFilter_end2end_latencies = ()
    dataFilter_end2end_latencies = (
        TileCombiner("receiver.synchronizer.latency_ms", "synchronizer latency", "max", combined=True) +
        TileCombiner("receiver.pc.renderer.*.latency_ms", "renderer latency", "min", combined=True) +
        TileCombiner("receiver.pc.renderer.*.latency_max_ms", "max renderer latency", "max", combined=True)
        )
    dataframe_end2end_latencies = dataFilter_end2end_latencies(dataframe_end2end_latencies)
    dataframe_end2end_latencies.interpolate().plot(x="sessiontime", y=["synchronizer latency", "renderer latency", "max renderer latency"], ax=ax, color=["blue", "red", "yellow"])
    # Limit Y axis to reasonable values
    max_latency = dataframe_end2end_latencies["renderer latency"].max()
    max_max_latency = dataframe_end2end_latencies["max renderer latency"].max()
    max_sync_latency = dataframe_end2end_latencies["synchronizer latency"].max()
    max_latency = max(max_latency, max_max_latency, max_sync_latency)
    # Limit Y axis to reasonable values
    if max_y != 0:
        ax.set_ylim(0, max_y)
    else:
        ax.set_ylim(0, max_latency*1.1)
    ax.set_xlim(0, 60)
    handles, labels = pyplot.gca().get_legend_handles_labels()
    nrows = -(-len(labels) // ncols)  # Ceiling division
    reordered_handles = handles
    reordered_labels = [label.capitalize() for label in labels]
    
    if use_row_major and ncols > 1:
        reordered_handles = []
        reordered_labels = []
        for i in range(ncols):
            for j in range(nrows):
                index = i + j * ncols
                print(index)
                if index < len(labels):
                    reordered_handles.append(handles[index])
                    print(handles[index].get_color())
                    reordered_labels.append(labels[index].capitalize())
    ax.legend(reordered_handles[::-1], reordered_labels[::-1], loc='upper left', fontsize='small', prop=legend_dict, labelspacing=labelspacing, ncols=ncols)
    if not show_legend:
        ax.legend().set_visible(False)
    pyplot.xticks(**tick_dict)
    pyplot.yticks(**tick_dict)
    pyplot.xlabel("Session time (s)", **label_dict)
    pyplot.ylabel("Latency (ms)", **label_dict)
    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, file_name), dpi, format=format)
    if showplot:
        pyplot.show() # type: ignore
        
    #
    # Save to csv file, in raw form
    #
    if savecsv:
        assert dirname
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
        dataframe_end2end_latencies = ds.get_dataframe(predicate=predicate, fields=fields)
        dataframe_end2end_latencies.to_csv(os.path.join(dirname, "latencies.csv"))    
    return ax

def plot_framerates(ds : DataStore, plotargs : Dict[str, Any]={}) -> Axes:
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
    ax1 = _plot_dataframe(df, 
        noshow=True,
        title="Frames per second", 
        x="sessiontime",
        descr=ds.annotator.description(),
        plotargs=plotargs
        )
    return ax1

def plot_framerates_dropped(ds : DataStore, plotargs : Dict[str, Any]={}) -> Axes:
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
        datafilter=dataFilter,
        plotargs=plotargs
        )
    return ax2

def plot_framerates_and_dropped(ds : DataStore, dirname : Optional[str]=None, showplot : bool=True, saveplot: bool=False, savecsv : bool=False, plotargs : Dict[str, Any]={}) -> Tuple[Axes, Axes]:
    ax1 = plot_framerates(ds, plotargs=plotargs)
    ax2 = plot_framerates_dropped(ds, plotargs=plotargs)

    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, "framerates.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    #
    # Save to csv file, without combining
    #
    if savecsv:
        assert dirname
        predicate='component_role and "fps" in record'
        fields=['sessiontime', 'component_role.=fps', 'component_role.=fps_dropped']
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        df.to_csv(os.path.join(dirname, "framerates.csv"))    
    return ax1, ax2
    
def plot_progress(ds : DataStore, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False, savecsv : bool=False, plotargs : Dict[str, Any]={}) -> Axes:
    df = ds.get_dataframe(
        predicate='"aggregate_packets" in record and component_role',
        fields = ['sessiontime', 'component_role=aggregate_packets']
        )
    columns = list(df.keys())
    columns.sort()
    columns.remove('sessiontime')
    columns.remove('sender.pc.grabber') # It can drop frames without being a problem.
    marker=None
    ax=None
    for y in columns:
        color='black'
        marker=None
        markevery = 100
        markoffset = 0
        if '.0' in y:
            color='red'
            markoffset = 20
        elif '.1' in y:
            color='blue'
            markoffset = 40
        elif '.2' in y:
            color='green'
            markoffset = 60
        elif '.3' in y:
            color='purple'
            markoffset = 80
        if '.encoder' in y:
            marker = '+'
            markoffset += 3
        elif '.writer' in y:
            marker = '>'
            markoffset += 6
        elif '.decoder' in y:
            marker = 'o'
            markoffset += 9
        elif '.preparer' in y:
            marker = '<'
            markoffset += 12
        elif '.reader' in y:
            marker = '*'
            markoffset += 15
        series = df.loc[:, ["sessiontime", y]]
        # Some columns need to be adjusted
        if ds.annotator.nTiles > 1:
            if '.all' in y:
                series[y] = series[y] / ds.annotator.nTiles
            elif y == "sender.pc.encoder":
                series[y] = series[y] / (ds.annotator.nTiles*ds.annotator.nQualities)
        ax = series.interpolate(method='pad').plot(x="sessiontime", marker=marker, markevery=(markoffset, markevery), color=color, alpha=0.5, ax=ax, plotargs=plotargs)
    assert ax
    ax.legend(loc='upper left', fontsize='small') # type: ignore
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    descr = ds.annotator.description()
    ax.text(0.98, 0.98, descr, transform=ax.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props) # type: ignore
    ax.set_title("Pointcloud Progress") # type: ignore
    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, "progress.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax

def plot_progress_latency(ds : DataStore, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False, savecsv : bool=False, plotargs : Dict[str, Any]={}) -> Axes:
    df = ds.get_dataframe(
        predicate='"aggregate_packets" in record and component_role',
        fields = ['sessiontime', 'component_role=aggregate_packets']
        )
    df0 = dataframe_to_pcindex_latencies_for_tile(df, 0)
    ax = df0.plot(x="sessiontime", ax=ax, plotargs=plotargs)
    if 'receiver.pc.reader.1' in df:
        df1 = dataframe_to_pcindex_latencies_for_tile(df, 1)
        ax = df1.plot(x="sessiontime", ax=ax, plotargs=plotargs)
    if 'receiver.pc.reader.2' in df:
        df2 = dataframe_to_pcindex_latencies_for_tile(df, 2)
        ax = df2.plot(x="sessiontime", ax=ax, plotargs=plotargs)
    if 'receiver.pc.reader.3' in df:
        df3 = dataframe_to_pcindex_latencies_for_tile(df, 3)
        ax = df3.plot(x="sessiontime", ax=ax, plotargs=plotargs)
    assert not 'receiver.pc.reader.4' in df, "plot_progress_latency can only handle up to 4 tiles"

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    descr = ds.annotator.description()
    ax.text(0.98, 0.98, descr, transform=ax.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props) # type: ignore
    ax.set_title("Pointcloud Receiver latencies") # type: ignore

    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, "progress-latencies.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax


def plot_latencies_rev(ds : DataStore, dpi : float|Literal["figure"]="figure", format : str="pdf", file_name : str="latencies.pdf", title : str="Latency contributions (ms)", label_dict : Dict[str, Any]={}, tick_dict : Dict[str, Any]={}, legend_dict : Dict[str, Any]={}, labelspacing : float=0.5, ncols : int=1, use_row_major : bool=False, dirname : Optional[str]=None, showplot : bool=True, saveplot : bool=False, savecsv : bool=False, max_y : float=0, show_desc : bool=True, figsize : Tuple[int, int]=(6, 4), show_legend : bool=True) -> Axes:
    dataFilter = (
        TileCombiner("receiver.pc.grabber.encoder_queue_ms", "encoder queue", "mean", combined=True) +
        TileCombiner("receiver.pc.encoder.encoder_ms", "encoder", "mean", combined=True) +
        TileCombiner("receiver.pc.encoder.transmitter_queue_ms", "transmitter queue", "mean", combined=True) +
        #TileCombiner("receiver.pc.reader.*.receive_ms", "receivers", "mean", combined=True) +
        TileCombiner("sender.pc.decoder.*.decoder_queue_ms", "decoder queues", "mean", combined=True) +
        TileCombiner("sender.pc.decoder.*.decoder_ms", "decoders", "max", combined=True) +
        TileCombiner("sender.pc.renderer.*.renderer_queue_ms", "renderer queues", "mean", combined=True)
        )
        
    #fig = pyplot.figure()
    ax = plot_simple(ds, 
        noshow=True,
        title="", 
        predicate='"receiver.pc.grabber" in component_role or "receiver.pc.encoder" in component_role or "sender.pc.decoder" in component_role or "sender.pc.renderer" in component_role or component_role == "sender.voice.renderer"', 
        fields  =[
            'component_role.=encoder_queue_ms',
            'component_role.=encoder_ms',
            'component_role.=transmitter_queue_ms',
            #'component_role.=receive_ms',
            'component_role.=decoder_queue_ms',
            'component_role.=decoder_ms',
            'component_role.=renderer_queue_ms'
            ],
        datafilter = dataFilter,
        plotargs=dict(kind="area", colormap="Paired", figsize=figsize),
        show_desc=show_desc
        )
    df = ds.get_dataframe(
        predicate='"sender.pc.renderer" in component_role or "sender.synchronizer" in component_role', 
        fields=[
            'sessiontime',
            'component_role.=latency_ms',
            'component_role.=latency_max_ms',
            ],
        )
    dataFilter2 = ()
    avg_latency = 0
    if show_sync:
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
    else:
        dataFilter2 = (
            TileCombiner("sender.pc.renderer.*.latency_ms", "renderer latency", "min", combined=True) +
            TileCombiner("sender.pc.renderer.*.latency_max_ms", "max renderer latency", "max", combined=True)
            )
        df = dataFilter2(df)
        df.interpolate().plot(x="sessiontime", y=["renderer latency", "max renderer latency"], ax=ax, color=["red", "yellow"])
        # Limit Y axis to reasonable values
        avg_latency = df["renderer latency"].mean()
        avg_max_latency = df["max renderer latency"].mean()
        avg_latency = max(avg_latency, avg_max_latency)
    # Limit Y axis to reasonable values
    if max_y != 0:
        ax.set_ylim(0, max_y)
    else:
        ax.set_ylim(0, avg_latency*2)
    ax.set_xlim(0, 60)
    handles, labels = pyplot.gca().get_legend_handles_labels()
    nrows = -(-len(labels) // ncols)  # Ceiling division
    reordered_handles = handles
    reordered_labels = [label.capitalize() for label in labels]
    if use_row_major and ncols > 1:
        reordered_handles = []
        reordered_labels = []
        for i in range(ncols):
            for j in range(nrows):
                index = i + j * ncols
                print(index)
                if index < len(labels):
                    reordered_handles.append(handles[index])
                    reordered_labels.append(labels[index].capitalize())
    ax.legend(reordered_handles[::-1], reordered_labels[::-1], loc='upper left', fontsize='small', prop=legend_dict, labelspacing=labelspacing, ncols=ncols) # type: ignore
    if not show_legend:
        ax.legend().set_visible(False) # type: ignore
    pyplot.xticks(**tick_dict) # type: ignore
    pyplot.yticks(**tick_dict) # type: ignore
    pyplot.xlabel("Session time (s)", **label_dict) # type: ignore
    pyplot.ylabel("Latency (ms)", **label_dict) # type: ignore
    if saveplot:
        assert dirname
        _save_multi_plot(os.path.join(dirname, file_name), dpi, format=format)
    if showplot:
        pyplot.show() # type: ignore
        
    #
    # Save to csv file, in raw form
    #
    if savecsv:
        assert dirname
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
