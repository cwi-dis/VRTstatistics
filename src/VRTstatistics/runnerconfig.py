
__all__ = ["defaultRunnerConfig"]

defaultRunnerConfig = {
    "sap.local": dict(
        statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
        logPath="Library/Logs/i2Cat/VRTogether/Player.log",
        user="jack",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-mmsys.app/Contents/MacOS/VRTogether",
        useSsh=True,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "sap-via-server": dict(
        statPath="Library/Application Support/i2Cat/VRTogether/statistics.log",
        logPath="Library/Logs/i2Cat/VRTogether/Player.log",
        user="jack",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-mmsys.app/Contents/MacOS/VRTogether",
        useSsh=False,
        host="sap.local",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "flauwte.local": dict(
        statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
        logPath="Library/Application\\ Support/i2Cat/VRTogether/Player.log",
        useSsh=True,
        user="jack",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrtiny.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="vrtogether",
        exePath="c:/Users/VRTogether/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrsmall.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log",
        user="vr-together",
        exePath="c:/Users/VR-Together/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
   ),
    "vrbig.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="vrtogether",
        exePath="c:/Users/VRTogether/Desktop/dev/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "fiddlehead": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="vr-together",
        host="fiddlehead.huiskamer.private",
        exePath="c:/Users/VR-Together/Desktop/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "arugula": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="vrtogether",
        host="arugula.huiskamer.private",
        exePath="c:/Users/VRTogether/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "scallion.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log",
        user="vrtogether",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "valkenburg-win10.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="dis",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
}
