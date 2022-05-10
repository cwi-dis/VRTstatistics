
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
    "sap": dict(
        statPath="Library/Application Support/i2Cat/VRTogether/statistics.log",
        logPath="Library/Logs/i2Cat/VRTogether/Player.log",
        user="jack",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-mmsys.app/Contents/MacOS/VRTogether",
        useSsh=False,
        host="sap.local",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "flauwte": dict(
        statPath="Library/Application Support/i2Cat/VRTogether/statistics.log",
        logPath="Library/Logs/i2Cat/VRTogether/Player.log",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-mmsys.app/Contents/MacOS/VRTogether",
        useSsh=False,
        host="flauwte.local",
        user="jack",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrtiny": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="vrtogether",
        exePath="C:/Users/vrtogether/VRTogether/VRTogether-built-measurements/VRTogether.exe",
        host="vrtiny.local",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrsmall": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log",
        user="vrtogether",
        host="vrsmall.huiskamer.private",
        exePath="C:/Users/vrtogether/VRTogether/VRTogether-built-measurements/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
   ),
    "vrbig": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        logPath="AppData/LocalLow/i2Cat/VRTogether/Player.log", 
        user="vrtogether",
        host="vrbig.huiskamer.private",
        exePath="C:/Users/vrtogether/VRTogether/VRTogether-built-measurements/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "carrageen": dict(
        statPath="/home/dis/.config/unity3d/i2Cat/VRTogether/statistics.log", 
        logPath="/home/dis/.config/unity3d/i2Cat/VRTogether/Player.log", 
        user="dis",
        host="carrageen.huiskamer.private",
        exePath="/home/dis/src/VRTogether/VRTogether-built-measurements/VRTogether.x86_64",
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
