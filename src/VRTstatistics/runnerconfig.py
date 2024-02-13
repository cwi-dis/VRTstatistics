
__all__ = ["defaultRunnerConfig"]

defaultRunnerConfig = {
    "flauwte.local": dict(
        statPath="Library/Application\\ Support/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt",
        logPath="Library/Logs/dis_cwi_nl/VR2Gather/Player.log",
        user="jack",
        useSsh=True,
    ),
    "vrtiny": dict(
        statPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt", 
        logPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/Player.log", 
        user="vrtogether",
        host="vrtiny.local",
        useSsh=False,
    ),
    "vrtiny.local": dict(
        statPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt", 
        logPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/Player.log", 
        user="vrtogether",
        host="vrtiny.local",
        useSsh=True,
    ),
    "sap.local": dict(
        statPath="Library/Application\\ Support/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt",
        logPath="Library/Logs/dis_cwi_nl/VR2Gather/Player.log",
        user="jack",
        useSsh=True,
    ),
    "beelzebub.local": dict(
        statPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/VQEG_Experiment.txt", 
        logPath="AppData/LocalLow/dis_cwi_nl/VR2Gather/Player.log", 
        user="dis",
        host="beelzebub.local",
        useSsh=True,
    ),

}
