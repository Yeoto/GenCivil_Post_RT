from ExportOptFile import ExportOptFile
import sys
from os import path
from os import listdir
from shutil import copyfile
import subprocess

from PostTableDiffer import PostTableDiffer

EXPORT_NEW_DATA = True

class GenCivilPostRT:
    Base_Cvl_Exe_Path = ''
    Test_Cvl_Exe_Path = ''
    Export_Path = ''
    Report_Path = ''
    file_list = []
    Tolerance = float

    def __init__(self) -> None:
        Tolerance = 1.0e-10
        return

    def Initialize(self, argv:list) -> bool:
        if len(argv) < 7:
            return False

        self.Base_Cvl_Exe_Path = argv[1]
        self.Test_Cvl_Exe_Path = argv[2]

        if not path.isfile(self.Test_Cvl_Exe_Path):
            return False

        if not path.isfile(self.Base_Cvl_Exe_Path):
            self.Base_Cvl_Exe_Path = ''

        Model_From_Path = argv[3]
        self.file_list = [path.join(Model_From_Path, f) for f in listdir(Model_From_Path) if path.splitext(f)[1] == '.mcb' and path.isfile(path.join(Model_From_Path, f))]
        if len(self.file_list) == 0:
            return False

        self.Export_Path = argv[4]
        self.Report_Path = argv[5]

        if len(argv) >= 6:
            self.Tolerance = float(argv[6])

        return True

    def PrintDescription(self):
        print('Parameters: "Base Civil Path" "Test Target Civil Path" "Model File Path" "Export Result File Path" "Export Report File Path" "Tolerance"')
        return

    def Run(self) -> bool:
        FESOptFile = ExportOptFile(self.Export_Path, "FES")
        FESOptFile.Export(EXPORT_NEW_DATA and self.Base_Cvl_Exe_Path != '')

        FES_Src_Path, FES_Tgt_Path, FES_Opt_FullPath = FESOptFile.GetPath()

        MECOptFile = ExportOptFile(self.Export_Path, "MEC")
        MECOptFile.Export(EXPORT_NEW_DATA)

        MEC_Src_Path, MEC_Tgt_Path, MEC_Opt_FullPath = MECOptFile.GetPath()

        if FES_Src_Path != MEC_Src_Path:
            return False

        for file in self.file_list:
            file_name = path.basename(file)
            copyfile(file, FES_Src_Path + "\\" + file_name)

        print('Exporting Data...')
        if EXPORT_NEW_DATA == True:
            if self.Base_Cvl_Exe_Path != '':
                subprocess.run([self.Base_Cvl_Exe_Path, '/PRT', FES_Opt_FullPath])
            subprocess.run([self.Test_Cvl_Exe_Path, '/PRT', MEC_Opt_FullPath])
        print('Exporting Data...Done!')

        FES_Result_list = [path.join(FES_Tgt_Path, f) for f in listdir(FES_Tgt_Path) if path.splitext(f)[1] == '.csv' and path.isfile(path.join(FES_Tgt_Path, f))]
        MEC_Result_list = [path.join(MEC_Tgt_Path, f) for f in listdir(MEC_Tgt_Path) if path.splitext(f)[1] == '.csv' and path.isfile(path.join(MEC_Tgt_Path, f))]

        print('Find Difference From Table Result File...')
        Differ = PostTableDiffer(self.Tolerance)
        Differ.InitializeTableData(FES_Result_list, MEC_Result_list)
        Differ.RunDiff(self.Report_Path)
        print('Find Difference From Table Result File...Done!')
        return True

if __name__ == "__main__":
    PostRT = GenCivilPostRT()

    if not PostRT.Initialize(sys.argv):
        PostRT.PrintDescription()
        sys.exit(-1)

    if not PostRT.Run():
        sys.exit(-1)

    sys.exit(0)