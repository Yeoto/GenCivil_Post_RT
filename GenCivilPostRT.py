from ast import arg
from ExportOptFile import ExportOptFile
import sys
from os import path
from os import listdir
from shutil import copyfile

class GenCivilPostRT:
    Base_Cvl_Exe_Path = ''
    Test_Cvl_Exe_Path = ''
    Export_Path = ''
    file_list = []

    def __init__(self) -> None:
        return

    def Initialize(self, argv:list) -> bool:
        if len(argv) < 4:
            return False

        self.Base_Cvl_Exe_Path = argv[1]
        self.Test_Cvl_Exe_Path = argv[2]

        if not path.isfile(self.Base_Cvl_Exe_Path) or not path.isfile(self.Test_Cvl_Exe_Path):
            return False

        self.Export_Path = argv[3]
        self.file_list = [path.join(self.Export_Path, f) for f in listdir(self.Export_Path) if path.splitext(f)[1] == '.mcb' and path.isfile(path.join(self.Export_Path, f))]

        if len(self.file_list) == 0:
            return False

        return True

    def PrintDescription(self):
        print('Parameters: "Base Civil Path" "Test Target Civil Path" "Model File Path"')
        return

    def Run(self) -> bool:
        FESOptFile = ExportOptFile()
        FESOptFile.Initialize(self.Export_Path, "FES")
        FESOptFile.Export()

        FES_Src_Path, FES_Tgt_Path = FESOptFile.GetPath()

        MECOptFile = ExportOptFile()
        MECOptFile.Initialize(self.Export_Path, "MEC")
        MECOptFile.Export()

        MEC_Src_Path, MEC_Tgt_Path = MECOptFile.GetPath()

        if FES_Src_Path != MEC_Src_Path:
            return False

        for file in self.file_list:
            file_name = path.basename(file)
            copyfile(file, FES_Src_Path + "\\" + file_name)

        return True
if __name__ == "__main__":
    PostRT = GenCivilPostRT()

    if not PostRT.Initialize(sys.argv):
        PostRT.PrintDescription()
        quit(-1)

    if not PostRT.Run():
        quit(-1)

    quit(0)