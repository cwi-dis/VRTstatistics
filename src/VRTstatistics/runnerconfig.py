
__all__ = ["defaultRunnerConfig"]

defaultRunnerConfig = {
    "flauwte.local": dict(
        statPath="Library/Application\\ Support/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt",
        logPath="Library/Logs/dis_cwi_nl/VR2Gather/Player.log",
        user="jack",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-vqeg.app/Contents/MacOS/VR2Gather",
        useSsh=True,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrtiny": dict(
        statPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt", 
        logPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/Player.log", 
        user="vrtogether",
        exePath="C:/Users/vrtogether/VRTogether/VRTogether-built-measurements/VR2Gather.exe",
        host="vrtiny.local",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),
    "vrtiny.local": dict(
        statPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt", 
        logPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/Player.log", 
        user="vrtogether",
        exePath="C:/Users/vrtogether/VRTogether/VRTogether-built-measurements/VR2Gather.exe",
        host="vrtiny.local",
        useSsh=False,
        exeArgs=["-vrmode", "None", "-disableVR"]
    ),

}
