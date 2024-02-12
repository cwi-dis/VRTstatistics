import VRTstatistics
from VRTstatistics.datastore import DataStore
from VRTstatistics import plots

def main():
    ds = DataStore("combined.json")
    ds.load()

    plots.plot_latencies(ds, "rabarber", showplot=True)

if __name__ == '__main__':
    main()