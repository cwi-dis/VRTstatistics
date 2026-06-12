import os
from typing import Tuple, Optional, List, Dict, Any, cast, Literal
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as pyplot
from matplotlib.backends.backend_pdf import PdfPages

from .datastore import DataStore, DataStoreError, Predicate
from .analyze import DataFrameFilter, TileCombiner, SessionTimeFilter
from .annotation import engine
from .views import (
    LatencyView, LatencyPerTileView, ResourceView, FramerateView, PointcountView, ProgressView,
    extract_latencies, extract_latencies_per_tile, extract_resources,
    extract_framerates, extract_pointcounts, extract_progress,
)

__all__ = [
    "plot_simple",
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
    "plot_latencies_per_tile",
    "render_latencies",
    "render_latencies_per_tile",
    "render_resources",
    "render_resource_cpu",
    "render_resource_mem",
    "render_resource_bandwidth",
    "render_framerates",
    "render_framerates_dropped",
    "render_framerates_and_dropped",
    "render_pointcounts",
    "render_progress",
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
        descr = datastore.describe()
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


def render_resource_cpu(view: ResourceView) -> Axes:
    """Render CPU usage from a ResourceView."""
    cpu_cols = [c for c in view.resources.columns if c != 'sessiontime' and c.endswith('.cpu')]
    ax = _plot_dataframe(view.resources, noshow=True, title="CPU usage", x="sessiontime", fields=cpu_cols, descr=view.description)
    _, top = ax.get_ylim()
    ax.set_ylim(0, top * 1.5)
    return ax


def render_resource_mem(view: ResourceView) -> Axes:
    """Render memory usage from a ResourceView."""
    mem_cols = [c for c in view.resources.columns if c != 'sessiontime' and c.endswith('.mem')]
    ax = _plot_dataframe(view.resources, noshow=True, title="Memory usage", x="sessiontime", fields=mem_cols, descr=view.description)
    _, top = ax.get_ylim()
    ax.set_ylim(0, top * 1.5)
    return ax


def render_resource_bandwidth(view: ResourceView) -> Axes:
    """Render bandwidth usage from a ResourceView."""
    bw_cols = [c for c in view.resources.columns if c != 'sessiontime' and (c.endswith('.recv_bandwidth') or c.endswith('.sent_bandwidth'))]
    ax = _plot_dataframe(view.resources, noshow=True, title="Bandwidth usage", x="sessiontime", fields=bw_cols, descr=view.description)
    _, top = ax.get_ylim()
    ax.set_ylim(0, top * 1.5)
    return ax


def render_resources(view: ResourceView, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False) -> Tuple[Axes, Axes, Axes]:
    """Render CPU, memory, and bandwidth subplots from a ResourceView."""
    ax1 = render_resource_cpu(view)
    ax2 = render_resource_mem(view)
    ax3 = render_resource_bandwidth(view)
    if saveplot:
        if not dirname:
            raise DataStoreError("saveplot=True requires dirname to be set")
        _save_multi_plot(os.path.join(dirname, "resources.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax1, ax2, ax3


def plot_latencies_for_tile(df : pd.DataFrame, tilenum : int, ax : Axes, sender : str="sender", receiver : str="receiver") -> Axes:
    fields = [
        f"{sender}.pc.grabber.downsample_ms",
        f"{sender}.pc.grabber.encoder_queue_ms",
        f"{sender}.pc.encoder.encoder_ms",
        f"{sender}.pc.encoder.transmitter_queue_ms",
        f"{receiver}.pc.reader.{tilenum}.receive_ms",
        f"{receiver}.pc.decoder.{tilenum}.decoder_queue_ms",
        f"{receiver}.pc.decoder.{tilenum}.decoder_ms",
        f"{receiver}.pc.renderer.{tilenum}.renderer_queue_ms"
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
        f"{receiver}.synchronizer.latency_ms",
        f"{receiver}.pc.renderer.{tilenum}.latency_ms",
        f"{receiver}.pc.renderer.{tilenum}.latency_max_ms",
        ]
    ax = df.interpolate(method='pad').plot(x="sessiontime", y=fields, kind="area", colormap="Paired", ax=ax, legend=False)
    df.interpolate(method='pad').plot(x="sessiontime", y=latency_fields, ax=ax, color=["blue", "red", "yellow"], legend=False)
    ax.set_title(f"Per-tile Latency contributions, tile={tilenum}") # type: ignore
    return ax


def render_latencies_per_tile(view: LatencyPerTileView, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False) -> List[Axes]:
    """Render per-tile latency subplots from a LatencyPerTileView."""
    fig : Figure
    axs : List[Axes]
    fig, axs = pyplot.subplots(view.nTiles, 1, sharex=True, sharey=True) # type: ignore
    fig.set_figheight(fig.get_figheight() * (view.nTiles - 1))
    fig.set_figwidth(fig.get_figwidth() * 1.5)
    for i in range(view.nTiles):
        plot_latencies_for_tile(view.per_tile, i, axs[i], sender=view.sender, receiver=view.receiver)
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right') # type: ignore
    pyplot.subplots_adjust(right=0.66)
    if saveplot:
        if not dirname:
            raise DataStoreError("saveplot=True requires dirname to be set")
        _save_multi_plot(os.path.join(dirname, "latencies-per-tile.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return axs


def render_latencies(view: LatencyView, dpi: float|Literal["figure"]="figure", format: str="pdf", file_name: str="latencies.pdf", title: str="Latency contributions (ms)", label_dict: Dict[str, Any]={}, tick_dict: Dict[str, Any]={}, legend_dict: Dict[str, Any]={}, labelspacing: float=0.5, ncols: int=1, use_row_major: bool=False, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False, max_y: float=0, show_desc: bool=True, figsize: Tuple[int, int]=(6, 4), show_legend: bool=True, show_disruptions: bool=False, plotargs: Dict[str, Any]={}) -> Axes:
    """
    Render latency contributions from a LatencyView.

    Produces a stacked area plot of pipeline stage durations with end-to-end latency
    line overlays. Optionally overlays disruption events (frame drops, tile switches).
    """
    descr = view.description if show_desc else None
    ax = _plot_dataframe(view.area,
        noshow=True,
        title=title,
        x="sessiontime",
        descr=descr,
        plotargs=dict(kind="area", colormap="Paired", figsize=figsize) | plotargs,
    )
    #
    # Overlay end-to-end latency lines
    #
    latency_cols = ["synchronizer latency", "renderer latency", "max renderer latency"]
    latency_colors = ["blue", "red", "yellow"]
    if "voice latency" in view.end2end.columns:
        latency_cols.append("voice latency")
        latency_colors.append("green")
    view.end2end.interpolate().plot(x="sessiontime", y=latency_cols, ax=ax, color=latency_colors)
    #
    # Overlay disruption event markers
    #
    if show_disruptions:
        if view.framedrops is not None:
            view.framedrops.plot(x='sessiontime', y=['PC Drop event'], marker='|', linestyle='None', color='red', ax=ax, zorder=4)
        if view.tileswitches is not None:
            view.tileswitches.plot(x='sessiontime', y=['Tile switch event'], marker='x', linestyle='None', color='blue', ax=ax, zorder=5)
    #
    # Y-axis limits
    #
    max_latency = view.end2end["renderer latency"].max()
    max_max_latency = view.end2end["max renderer latency"].max()
    max_sync_latency = view.end2end["synchronizer latency"].max()
    max_latency = max(max_latency, max_max_latency, max_sync_latency)
    if "voice latency" in view.end2end.columns:
        max_voice_latency = view.end2end["voice latency"].max()
        if not pd.isna(max_voice_latency):
            max_latency = max(max_latency, max_voice_latency)
    if max_y != 0:
        ax.set_ylim(0, max_y)
    else:
        ax.set_ylim(0, max_latency * 1.1)
    ax.set_xlim(left=0)
    #
    # Legend (optionally multi-column, optionally row-major ordering)
    #
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
                if index < len(labels):
                    reordered_handles.append(handles[index])
                    reordered_labels.append(labels[index].capitalize())
    ax.legend(reordered_handles[::-1], reordered_labels[::-1], loc='upper left', fontsize='small', prop=legend_dict, labelspacing=labelspacing, ncols=ncols)
    if not show_legend:
        ax.legend().set_visible(False)
    pyplot.xticks(**tick_dict)
    pyplot.yticks(**tick_dict)
    pyplot.xlabel("Session time (s)", **label_dict)
    pyplot.ylabel("Latency (ms)", **label_dict)
    if saveplot:
        if not dirname:
            raise DataStoreError("saveplot=True requires dirname to be set")
        _save_multi_plot(os.path.join(dirname, file_name), dpi, format=format)
    if showplot:
        pyplot.show() # type: ignore
    return ax


def render_framerates(view: FramerateView, plotargs: Dict[str, Any]={}) -> Axes:
    """Render frames-per-second from a FramerateView."""
    return _plot_dataframe(view.fps, noshow=True, title="Frames per second", x="sessiontime", descr=view.description, plotargs=plotargs)


def render_framerates_dropped(view: FramerateView, plotargs: Dict[str, Any]={}) -> Axes:
    """Render dropped-frames-per-second from a FramerateView."""
    return _plot_dataframe(view.fps_dropped, noshow=True, title="FPS dropped", x="sessiontime", descr=view.description, plotargs=plotargs)


def render_framerates_and_dropped(view: FramerateView, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False, plotargs: Dict[str, Any]={}) -> Tuple[Axes, Axes]:
    """Render fps and dropped-fps subplots from a FramerateView."""
    ax1 = render_framerates(view, plotargs=plotargs)
    ax2 = render_framerates_dropped(view, plotargs=plotargs)
    if saveplot:
        if not dirname:
            raise DataStoreError("saveplot=True requires dirname to be set")
        _save_multi_plot(os.path.join(dirname, "framerates.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax1, ax2


def render_pointcounts(view: PointcountView, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False) -> Axes:
    """Render receiver point counts from a PointcountView."""
    ax = _plot_dataframe(view.pointcounts, noshow=True, title="Receiver point counts", x="sessiontime", descr=view.description)
    _, top = ax.get_ylim()
    ax.set_ylim(0, top * 1.5)
    if saveplot:
        if not dirname:
            raise DataStoreError("saveplot=True requires dirname to be set")
        _save_multi_plot(os.path.join(dirname, "pointcounts.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax


def render_progress(view: ProgressView, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False, plotargs: Dict[str, Any]={}) -> Axes:
    """Render point cloud pipeline progress from a ProgressView."""
    df = view.progress
    columns = [c for c in df.columns if c != 'sessiontime']
    ax = None
    for y in columns:
        color = 'black'
        marker = None
        markevery = 100
        markoffset = 0
        if '.0' in y:
            color = 'red'
            markoffset = 20
        elif '.1' in y:
            color = 'blue'
            markoffset = 40
        elif '.2' in y:
            color = 'green'
            markoffset = 60
        elif '.3' in y:
            color = 'purple'
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
        ax = series.interpolate(method='pad').plot(x="sessiontime", marker=marker, markevery=(markoffset, markevery), color=color, alpha=0.5, ax=ax, **plotargs)
    assert ax
    ax.legend(loc='upper left', fontsize='small') # type: ignore
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.98, 0.98, view.description, transform=ax.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props) # type: ignore
    ax.set_title("Pointcloud Progress") # type: ignore
    if saveplot:
        if not dirname:
            raise DataStoreError("saveplot=True requires dirname to be set")
        _save_multi_plot(os.path.join(dirname, "progress.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    return ax


def plot_pointcounts(ds: DataStore, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False) -> Axes:
    return render_pointcounts(extract_pointcounts(ds), dirname=dirname, showplot=showplot, saveplot=saveplot)

def plot_resource_cpu(ds: DataStore) -> Axes:
    return render_resource_cpu(extract_resources(ds))

def plot_resource_mem(ds: DataStore) -> Axes:
    return render_resource_mem(extract_resources(ds))

def plot_resource_bandwidth(ds: DataStore) -> Axes:
    return render_resource_bandwidth(extract_resources(ds))

def plot_resources(ds: DataStore, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False) -> Tuple[Axes, Axes, Axes]:
    return render_resources(extract_resources(ds), dirname=dirname, showplot=showplot, saveplot=saveplot)

def plot_latencies_per_tile(ds: DataStore, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False) -> List[Axes]:
    return render_latencies_per_tile(extract_latencies_per_tile(ds), dirname=dirname, showplot=showplot, saveplot=saveplot)

def plot_latencies(ds: DataStore, dpi: float|Literal["figure"]="figure", format: str="pdf", file_name: str="latencies.pdf", title: str="Latency contributions (ms)", label_dict: Dict[str, Any]={}, tick_dict: Dict[str, Any]={}, legend_dict: Dict[str, Any]={}, labelspacing: float=0.5, ncols: int=1, use_row_major: bool=False, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False, max_y: float=0, show_desc: bool=True, figsize: Tuple[int, int]=(6, 4), show_legend: bool=True, show_disruptions: bool=False, plotargs: Dict[str, Any]={}) -> Axes:
    return render_latencies(extract_latencies(ds), dpi=dpi, format=format, file_name=file_name, title=title, label_dict=label_dict, tick_dict=tick_dict, legend_dict=legend_dict, labelspacing=labelspacing, ncols=ncols, use_row_major=use_row_major, dirname=dirname, showplot=showplot, saveplot=saveplot, max_y=max_y, show_desc=show_desc, figsize=figsize, show_legend=show_legend, show_disruptions=show_disruptions, plotargs=plotargs)

def plot_framerates(ds: DataStore, plotargs: Dict[str, Any]={}) -> Axes:
    return render_framerates(extract_framerates(ds), plotargs=plotargs)

def plot_framerates_dropped(ds: DataStore, plotargs: Dict[str, Any]={}) -> Axes:
    return render_framerates_dropped(extract_framerates(ds), plotargs=plotargs)

def plot_framerates_and_dropped(ds: DataStore, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False, plotargs: Dict[str, Any]={}) -> Tuple[Axes, Axes]:
    return render_framerates_and_dropped(extract_framerates(ds), dirname=dirname, showplot=showplot, saveplot=saveplot, plotargs=plotargs)

def plot_progress(ds: DataStore, dirname: Optional[str]=None, showplot: bool=True, saveplot: bool=False, plotargs: Dict[str, Any]={}) -> Axes:
    return render_progress(extract_progress(ds), dirname=dirname, showplot=showplot, saveplot=saveplot, plotargs=plotargs)
