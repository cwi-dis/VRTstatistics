# VRTstatistics example

This directory contains the files needed to gather some statistics from a two-machine VR2Gather run. It also contains the output files from a test run, so you don't have to do an experiment if you only want to look at the data analysis tools. 

## Preparing and running an experiment

### Preparing the test machines

- Select two machines on which to run the experiment. You may want a third machine to control things from, or you could use one of the machines used in the test. The control software is not very heavy so it won't influence the results.
	- In the sample configuration the machines used are `flauwte`, a Mac, and `vrtiny`, a Windows machine.
- On both machines, build the VR2Gather app you want to test. Remember the pathname of the executable.
- On both machines, run the built VR2Gather app once. Select a username, set to auto-login. In the _Settings_ dialog, select the self-representation and microphone you want to test.
- On both machines, check out this repository (`VRTstatistics`), open a CMD prompt (or, on Mac/Linux, a shell) and install the VRTstatistics package as per the instructions in the [top-level README](../readme.md).
- On both machines, run `VRTstatistics-runserver`. This is a little helper server that will start the VR2Gather applications and send all the log data back to the controlling machine.

	> **Note**: this is not a very secure server, so make sure it is not accessible from the outside world.
	>
	> **Note**: you should probably _not_ try to run the runserver over an ssh-connection. The runserver will start VR2Gather, and VR2Gather is going to need access to the display. Often this will not work when logged in remotely over ssh (no access to the display unless started from the display).

### Preparing the test configuration

- On the controlling machine, edit the VR2Gather configuration file`config.json`. This file will be forwarded to the test machines and used to control the session. Especially look at the `AutoStart` parameters and the `stats...` parameters.
- On the controlling machine, edit the VRTstatistics configuration `VRTstatistics-config.json` and fix all the pathnames. Using absolute paths is best. Check the example code for how to determine the pathnames on Windows/Mac.
  
  > **Note**: determining the path names of the output log file and the output statistics file seems to be a black art. Part of the pathnames is documented in the Unity documentation, but parts are obscure. For example, we have no idea why different conventions seem to be followed on Windows and MacOS. Nevertheless, they are typically to be found under `C:/Users/<username>/AppData/LocalLow/<Company Name>/<Product Name>/` (Windows), `/Users/<username>/Library/Application Support/<Company Name>.<Product Name>.<Build Name>/` (Mac, statPath) and `/Users/<username>/Library/Logs/<Company Name>/<Product Name>/` (Mac, logPath) with `<Company Name>, <Product Name> and <Build Name>` as set in `File > Build Settings` and `File > Build Settings > Player Settings` in Unity.
  > 
  > It seems to be best to try one run, them search in the relevant directories (`AppData` on Windows, `Library` on MacOS) for the files that you know have been created.

### Running a test

- Ensure the test machines have `VRTstatistics-runserver` running. Ensure they don't have too many other applications running that could influence performance. Specifically: you should probably not run Remote Desktop or anything like that.
- On the controlling machine, create a directory to store the results. Something like `results-yymmdd-hhmmss`.
- On the controlling machine, start the session with something like

```
VRTstatistics-ingest --destdir results-20240705-1155/ --vrtconfig config.json --config VRTstatistics-config.json --run --annotator latency flauwte.local vrtiny.local
```

- This should run the session at the two test machines. For the first (or first few) runs it is probably a good idea to be able to see the screens of the test machines, allowing you to see what is happening.
  
  > ... even if this means that you have to have a Windows Remote Desktop open to the machine, which will influence the results. That means the results won't be as trustworthy but at least you know what is happening.
  
- This should provide you with the files from the next section. In case you get errors from `VRTstatistics-ingest` about missing files you probably have mis-typed one or more of the filenames. Looking at the output from the two `VRTstatistics-runserver` commands may be of help here.

### Resulting raw data files

For each of the two machines you should get:

- the unity logs `sender-unity-log.txt` and `receiver-unity-log.txt`(which you need only for debugging in case things went wrong), 
- the statistics files `sender.log` and `receiver.log` which contain most of the interesting data in raw form,
- the resource usage files `sender-rusage.log` and `receiver-rusage.log`, which are in the same form as the statistics files, but measured completely different: they contain overall system CPU, bandwidth and memory usage data.

### Results database

There is also the file `combined.json` which contains all data from the previous 4 `.log` files. This is the database that will be used by the analysis tools, below.

This file can always we re-created from the logfiles by running 

```
VRTstatistics-ingest --destdir results-20240705-1155/ --nofetch flauwte.local vrtiny.local
```

The results database can also be re-created using a different annotator, in case you are interested in different data from the raw data:

```
VRTstatistics-ingest --destdir results-20240705-1155/ --nofetch --annotator latency flauwte.local vrtiny.local
```

The `latency` annotator will measure latencies of voice and point cloud data flowing from the `sender` to the `receiver` (so uni-directionally).

## Analysing the data

A first quick way to visualize one-way latencies is the following command:

```
VRTstatistics-plot --datastore results-20240705-1155/combined.json --predicate "'latency_ms' in record and component_role" component_role=latency_ms
```

This will select all records that contain a `latency_ms` field, and also have a non-empty `component_role` field. These latencies are then plotted.
