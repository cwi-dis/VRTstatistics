
__all__ = ["defaultRunnerConfig"]

defaultRunnerConfig = {
    "sap.local": dict(
        statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
        user="jack",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-mmsys.app/Contents/MacOS/VRTogether",
        useSsh=True,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "flauwte.local": dict(
        statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
        useSsh=True,
        user="jack",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrtiny.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        user="vrtogether",
        exePath="c:/Users/VRTogether/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrsmall.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="vr-together",
        exePath="c:/Users/VR-Together/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
   ),
    "vrbig.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        user="vrtogether",
        exePath="c:/Users/VRTogether/Desktop/dev/VRTapp-built-mmsys/VRTogether.exe",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "scallion.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="vrtogether",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "valkenburg-win10.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        user="dis",
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
}
