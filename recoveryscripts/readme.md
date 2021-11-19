# stats recovery script

This script might help if you have accidentally deleted your log files and managed to salvage some data with a tool like `Windows File Recovery` or (better) `PhotoRec`.

It will look through salvaged text files, which will probably also contain data that has been overwritten, and it will copy the portions of the file that seem to contain `stats:` data.

As the file names have been lost at this point the output file name will be based on the first `ts=` timestamp found in the data.