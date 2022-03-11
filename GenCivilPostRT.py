from ExportOptFile import ExportOptFile
import sys
from os import path
from os import listdir
from shutil import copyfile
import subprocess
from datetime import datetime

from PostTableDiffer import PostTableDiffer
from MyUtils import MyEmaillib, MyZiplib

EXPORT_NEW_DATA = False

class GenCivilPostRT:
    Base_Cvl_Exe_Path = ''
    Test_Cvl_Exe_Path = ''
    Export_Path = ''
    Report_Path = ''
    file_list = []
    Val_Tolerance = float
    Per_Tolerance = float

    MailTo = list[str]
    Origin_Cvl_Path = ''
    Origin_Solver_Path = ''
    Origin_Model_Path = ''

    def __init__(self) -> None:
        Val_Tolerance = 1.0e-6
        Per_Tolerance = 0.1
        return

    def Initialize(self, argv:list) -> bool:
        if len(argv) < 10:
            return False

        self.Base_Cvl_Exe_Path = argv[1]
        self.Test_Cvl_Exe_Path = argv[2]

        if not path.isfile(self.Test_Cvl_Exe_Path):
            return False

        if not path.isfile(self.Base_Cvl_Exe_Path):
            self.Base_Cvl_Exe_Path = ''

        self.Origin_Model_Path = argv[3]
        self.file_list = [path.join(self.Origin_Model_Path, f) for f in listdir(self.Origin_Model_Path) if path.splitext(f)[1] == '.mcb' and path.isfile(path.join(self.Origin_Model_Path, f))]
        if len(self.file_list) == 0:
            return False

        self.Export_Path = argv[4]
        self.Report_Path = argv[5] + ".xml"
        self.Error_Row_Path = argv[5] + ".xlsx"

        self.MailTo =  [f.strip() for f in argv[6].split(',') if f.strip() != '']

        self.Val_Tolerance = float(argv[7])
        self.Per_Tolerance = float(argv[8])

        self.Origin_Cvl_Path = argv[9]
        self.Origin_Solver_Path = argv[10]
        return True

    def PrintDescription(self):
        print('''
        Parameters: 
        "Base Civil Path" 
        "Test Target Civil Path" 
        "Model File Path" 
        "Export Result File Path" 
        "Export Report File Path" 
        "Mail To(seperate with ;)" 
        "Value Tolerance (1.0e-6)" 
        "Percentage Tolerance (0.1)" 
        "Report Civil Dll Path" 
        "Report Solver Dll Path" 
        ''')
        return

    def Run(self) -> bool:
        FESOptFile = ExportOptFile(self.Export_Path, "FES", ['UNIT_FORCE,N', 'UNIT_LENGTH,mm'])
        FESOptFile.Export(EXPORT_NEW_DATA and self.Base_Cvl_Exe_Path != '')

        FES_Src_Path, FES_Tgt_Path, FES_Opt_FullPath = FESOptFile.GetPath()

        MECOptFile = ExportOptFile(self.Export_Path, "MEC", ['UNIT_FORCE,N', 'UNIT_LENGTH,mm'])
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
        Differ = PostTableDiffer(self.Val_Tolerance, self.Per_Tolerance)
        Differ.InitializeTableData(FES_Result_list, MEC_Result_list)
        err_file_list = Differ.RunDiff(self.Report_Path, self.Error_Row_Path)
        print('Find Difference From Table Result File...Done!')

        self.ExportToMail(err_file_list, MEC_Result_list)
        return True

    def ExportToMail(self, err_file_list:list[str], Target_file_list:list[str]):
        zip_path = path.dirname(self.Report_Path) + '\\Exported Error Files.zip'
        MyZiplib.MakeZip(zip_path, err_file_list)

        if 'pyj0827' not in self.MailTo:
            self.MailTo.append('pyj0827')
        #if 'Joyang' not in self.MailTo:
        #    self.MailTo.append('Joyang')

        error_ratio = (len(err_file_list) / len(Target_file_list)) * 100

        MyEmaillib.Send_Report(self.MailTo, 
        '''
        Civil NS Post Table Regression Test Result
        Test Date : {0}
        Target Civil DLL Path : {1}
        Target Solver DLL Path : {2}
        Target Model File : {3}
        Error Model File Percentage : {4}%({5}/{6})
        '''. format(datetime.today().strftime('%Y-%m-%d'), self.Origin_Cvl_Path, self.Origin_Solver_Path, self.Origin_Model_Path, error_ratio, str(len(err_file_list)), str(len(Target_file_list))),
        [self.Report_Path, self.Error_Row_Path, zip_path])
        return 

if __name__ == "__main__":
    PostRT = GenCivilPostRT()

    if not PostRT.Initialize(sys.argv):
        PostRT.PrintDescription()
        sys.exit(-1)

    if not PostRT.Run():
        sys.exit(-1)

    sys.exit(0)