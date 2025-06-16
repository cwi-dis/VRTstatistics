import os
from typing import Tuple, Optional, Any
from matplotlib.axes import Axes
import pandas as pd
import matplotlib.pyplot as pyplot
from matplotlib.backends.backend_pdf import PdfPages

from .datastore import DataStore, DataStoreError
from .analyze import TileCombiner, SessionTimeFilter, dataframe_to_pcindex_latencies_for_tile

Predicate = str

__all__ = [
    "plot_simple", 
    "plot_dataframe", 
    "plot_framerates_and_dropped", 
    "plot_framerates_dropped", 
    "plot_framerates", 
    "plot_latencies", 
    ]

def plot_simple(datastore : DataStore, *, 
        predicate:Optional[Predicate]=None, 
        title:str=None, 
        noshow:bool=False, 
        x:str="sessiontime", 
        fields:Any=None, 
        datafilter=None, plotargs={}, show_desc=True) -> Axes:
    """
    Plot data (optionally after converting to pandas.DataFrame).
    output is optional output file (default: show in a window)
    x is name of x-axis field
    fields is list of fields to plot (default: all, except x)
    """
    fields_to_retrieve = list(fields)
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
    return plot_dataframe(dataframe, title=title, noshow=noshow, x=x, fields=fields_to_plot, descr=descr, plotargs=plotargs)

def plot_dataframe(dataframe : pd.DataFrame, *, title=None, noshow=False, x=None, fields=None, descr=None, plotargs={}, interpolate='linear') -> Axes:
    if dataframe.empty:
        raise DataStoreError("dataframe is empty, nothing to plot")
    if fields:
        plot = dataframe.interpolate(method=interpolate).plot(x=x, y=fields, **plotargs)
    else:
        plot = dataframe.interpolate(method=interpolate).plot(x=x, **plotargs)
    if descr:
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        plot.text(0.98, 0.98, descr, transform=plot.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props)
    if title:
        pyplot.title(title)
    plot.legend(loc='upper left', fontsize='small')
    if not noshow:
        pyplot.show()
    return plot
   
def plot_latencies(
        ds : DataStore, 
        dpi="figure", 
        format="pdf", 
        file_name="latencies.pdf", 
        title="Latency contributions (ms)", 
        label_dict={}, 
        tick_dict={}, 
        legend_dict={}, 
        labelspacing=0.5, 
        ncols=1, 
        use_row_major=False, 
        dirname=None, 
        showplot=True, 
        saveplot=False, 
        savecsv=False, 
        max_y=0, 
        show_sync=True, 
        show_desc=True, 
        figsize=(6, 4), 
        show_legend=True
        ) -> Axes:
    pyplot.close() # Close old figure
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
        
    #fig = pyplot.figure()
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
        plotargs=dict(kind="area", colormap="Paired", figsize=figsize),
        show_desc=show_desc
        )
    df = ds.get_dataframe(
        predicate='"receiver.pc.renderer" in component_role or "receiver.synchronizer" in component_role', 
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
            TileCombiner("receiver.pc.renderer.*.latency_ms", "renderer latency", "min", combined=True) +
            TileCombiner("receiver.pc.renderer.*.latency_max_ms", "max renderer latency", "max", combined=True)
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
        _save_multi_plot(os.path.join(dirname, file_name), dpi, format=format)
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

def plot_framerates(ds : DataStore) -> Axes:
    pyplot.close() # Close old figure
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

def plot_framerates_dropped(ds : DataStore) -> Axes:
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

def plot_framerates_and_dropped(
        ds : DataStore, 
        dirname : str, 
        showplot : bool = True, 
        saveplot : bool = False, 
        savecsv : bool = False
        ) -> Tuple[Axes, Axes]:
    pyplot.close() # Close old figure
    ax1 = plot_framerates(ds)
    ax2 = plot_framerates_dropped(ds)

    if saveplot:
        _save_multi_plot(os.path.join(dirname, "framerates.pdf"))
    if showplot:
        pyplot.show() # type: ignore
    #
    # Save to csv file, without combining
    #
    if savecsv:
        predicate='component_role and "fps" in record'
        fields=['sessiontime', 'component_role.=fps', 'component_role.=fps_dropped']
        df = ds.get_dataframe(predicate=predicate, fields=fields)
        df.to_csv(os.path.join(dirname, "framerates.csv"))    
    return ax1, ax2

def _save_multi_plot(filename : str, dpi : str = "figure", format : str = "pdf"):
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
    