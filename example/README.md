# VRTstatistics example

This directory contains the files needed to gather some statistics from a two-machine VR2Gather run.

Follow the steps here to try it.

### Preparing the test machines

- Select two machines on which to run the experiment. You may want a third machine to control things from, or you could use one of the machines used in the test. The control software is not very heavy so it won't influence the results.
	- In the sample configuration the machines used are `flauwte`, a Mac, and `vrtiny`, a Windows machine.
- On both machines, build the VR2Gather app you want to test. Remember the pathname of the executable.
- On both machines, run the built VR2Gather app once. Select a username, set to auto-login. In the _Settings_ dialog, select the self-representation and microphone you want to test.
- On both machines, check out this repository (`VRTstatistics`), open a CMD prompt (or, on Mac/Linux, a shell) and install the VRTstatistics package as per the instructions in the [top-level README](../README.md).
- On both machines, run `VRTstatistics-runserver`. This is a little helper server that will start the VR2Gather applications and send all the log data back to the controlling machine.

	> Note: this is not a very secure server, so make sure it is not accessible from the outside world.

### Preparing the test configuration

- On the controlling machine, edit the VRTstatistics configuration `VRTstatistics-config.json` and fix all the pathnames. Using absolute paths is best. Check the example code for how to determine the pathnames on Windows/Mac.
- On the controlling machine, edit the VR2Gather configuration file`config.json`. This file will be forwarded to the test machines and used to control the session.

### Running a test

- Ensure the test machines have `VRTstatistics-runserver` running. Ensure they don't have too many other applications running that could influence performance. Specifically: you should probably not run Remote Desktop or anything like that.
- On the controlling machine, create a directory to store the results. Something like `results-yymmdd-hhmmss`.
- On the controlling machine, start the session with something like

```
VRTstatistics-ingest --destdir results-20240604-1330/ --vrtconfig config.json --config VRTstatistics-config.json --run flauwte.local vrtiny.local
```
