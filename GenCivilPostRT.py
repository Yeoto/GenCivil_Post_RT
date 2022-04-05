import shutil
from ExportOptFile import ExportOptFile
import sys
import os
from os import path
from shutil import copyfile, rmtree
import subprocess
from datetime import datetime

from PostTableDiffer import PostTableDiffer
from MyUtils import MyEmaillib, MyZiplib

IS_DEBUG = True
EXPORT_NEW_DATA = not IS_DEBUG or False

class GenCivilPostRT:
    Base_Cvl_Exe_Path = ''
    Test_Cvl_Exe_Path = ''
    Export_Path = ''
    Report_Path = ''
    file_list_FES = {}
    file_list_MEC = {}
    Val_Tolerance = float
    Per_Tolerance = float

    MailTo = list[str]
    Origin_Cvl_Path = ''
    Origin_Solver_Path = ''
    Export_Share_Path = ''

    def __init__(self) -> None:
        Val_Tolerance = 1.0e-6
        Per_Tolerance = 0.1
        return

    def GetFileList(path):
        files = {}
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                folder_name = os.path.relpath(dirpath, path)
                if folder_name == '.':
                    folder_name = ""
                if folder_name not in files:
                    files[folder_name] = []
                files[folder_name].append(os.path.join(dirpath, f))
            
        return files
           #if isdir(f):
           #    self.Recursive_GetFile(f, folder_name + '\\' + basename(f))
           #if isfile(f):
           #    self.file_list[folder_name].append(f)

    def Initialize(self, argv:list) -> bool:
        if len(argv) < 12:
            return False

        self.Base_Cvl_Exe_Path = argv[1]
        self.Test_Cvl_Exe_Path = argv[2]

        if not path.isfile(self.Test_Cvl_Exe_Path):
            return False

        if not path.isfile(self.Base_Cvl_Exe_Path):
            self.Base_Cvl_Exe_Path = ''

        FES_Model_Path = argv[3]
        self.file_list_FES = GenCivilPostRT.GetFileList(FES_Model_Path)
        if len(self.file_list_FES) == 0:
            return False

        MEC_Model_Path = argv[4]
        self.file_list_MEC = GenCivilPostRT.GetFileList(MEC_Model_Path)
        if len(self.file_list_MEC) == 0:
            return False

        self.Export_Path = argv[5]
        self.Report_Path = os.path.join(self.Export_Path, argv[6])

        self.MailTo =  [f.strip() for f in argv[7].split(',') if f.strip() != '']

        self.Val_Tolerance = float(argv[8])
        self.Per_Tolerance = float(argv[9])

        self.Origin_Cvl_Path = argv[10]
        self.Origin_Solver_Path = argv[11]
        self.Export_Share_Path = os.path.join(argv[12], datetime.today().strftime('%Y%m%d_%H%M%S'))
        return True

    def PrintDescription(self):
        print('''
        Parameters: 
        "Base Civil Path" 
        "Test Target Civil Path" 
        "Base Model File Path" 
        "Target Model File Path" 
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
        if IS_DEBUG:
            print('''
            DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG 
            ''')

        if EXPORT_NEW_DATA == False:
            print('''
            NO EXPORT NEW DATA !!!!!!!!!!!!
            NO EXPORT NEW DATA !!!!!!!!!!!!
            NO EXPORT NEW DATA !!!!!!!!!!!!
            ''')

        #Export FES Result
        FES_Result_list = {}
        for folder, files in self.file_list_FES.items():
            FESOptFile = ExportOptFile(self.Export_Path, "FES", ['UNIT_FORCE,N', 'UNIT_LENGTH,mm'])
            FES_Src_Path, FES_Tgt_Path, FES_Opt_FullPath = FESOptFile.Export(EXPORT_NEW_DATA and self.Base_Cvl_Exe_Path != '', folder)

            if os.path.isdir(FES_Src_Path) and EXPORT_NEW_DATA == True:
                rmtree(FES_Src_Path)
                os.makedirs(FES_Src_Path)

            for file in files:
                file_name = os.path.basename(file)
                copyfile(file, os.path.join(FES_Src_Path, file_name))

            if IS_DEBUG == True:
                print('Exporting FES Result Data... ' + folder)

            if EXPORT_NEW_DATA == True and self.Base_Cvl_Exe_Path != '':
                subprocess.run([self.Base_Cvl_Exe_Path, '/PRT', FES_Opt_FullPath])

            if IS_DEBUG == True:
                print('Exporting FES Result Data... ' + folder + ' Done!')

            FES_Result_list[folder] = [os.path.join(FES_Tgt_Path, f) for f in os.listdir(FES_Tgt_Path) if path.splitext(f)[1] == '.csv' and path.isfile(path.join(FES_Tgt_Path, f))]

        #Export MEC Result
        MEC_Result_list = {}
        for (folder, files) in self.file_list_MEC.items():
            MECOptFile = ExportOptFile(self.Export_Path, "MEC", ['UNIT_FORCE,N', 'UNIT_LENGTH,mm'])
            MEC_Src_Path, MEC_Tgt_Path, MEC_Opt_FullPath = MECOptFile.Export(EXPORT_NEW_DATA, folder)

            if os.path.isdir(MEC_Src_Path) and EXPORT_NEW_DATA == True:
                rmtree(MEC_Src_Path)
                os.makedirs(MEC_Src_Path)

            for file in files:
                file_name = path.basename(file)
                copyfile(file, os.path.join(MEC_Src_Path, file_name))

            if IS_DEBUG == True:
                print('Exporting MEC Result Data... ' + folder)

            if EXPORT_NEW_DATA == True:
                subprocess.run([self.Test_Cvl_Exe_Path, '/PRT', MEC_Opt_FullPath])

            if IS_DEBUG == True:
                print('Exporting MEC Result Data... ' + folder + ' Done!')

            MEC_Result_list[folder] = [os.path.join(MEC_Tgt_Path, f) for f in os.listdir(MEC_Tgt_Path) if path.splitext(f)[1] == '.csv' and path.isfile(path.join(MEC_Tgt_Path, f))]

        #Clean Up Results
        if os.path.isdir(self.Export_Path):
            for f in os.listdir(self.Export_Path):
                if os.path.isfile(os.path.join(self.Export_Path, f)):
                    os.remove(os.path.join(self.Export_Path, f))

        #Diff
        Differ = PostTableDiffer(self.Val_Tolerance, self.Per_Tolerance)
        Error_Row_Paths = []
        err_file_list = []

        for folder in MEC_Result_list.keys():
            if folder not in FES_Result_list:
                continue

            FES_Result_files = FES_Result_list[folder]
            MEC_Result_files = MEC_Result_list[folder]

            Error_Row_Path = self.Report_Path + ("_" + folder.replace('\\', '_') if folder != "" else "") + ".xlsx"

            if IS_DEBUG == True:
                print('Paring Exported Result Data... ' + folder)

            Differ.InitializeTableData(FES_Result_files, MEC_Result_files)

            if IS_DEBUG == True:
                print('Paring Exported Result Data... ' + folder + ' Done!')

            cur_error_file_list = Differ.RunDiff(Error_Row_Path, IS_DEBUG=IS_DEBUG)

            if len(cur_error_file_list) > 0:
                Error_Row_Paths.append(Error_Row_Path)
                err_file_list.extend(cur_error_file_list)

        Differ.SaveJunit(self.Report_Path + ".xml")
        results = []
        for files_list in list(MEC_Result_list.values()):
            results.extend(files_list)
        self.ExportToMail(err_file_list, results, Error_Row_Paths)
        self.ExportToShareFolder(err_file_list, Error_Row_Paths)
        return True

    def ExportToMail(self, err_file_list:list[str], Target_file_list:list[str], Error_Row_Paths:list[str]):
        zip_path_Error_Files = self.Export_Path + '\\Exported Error Files.zip'
        MyZiplib.MakeZip(zip_path_Error_Files, err_file_list)

        zip_path_Error_Rows = self.Export_Path + '\\Exported Error Rows.zip'
        MyZiplib.MakeZip(zip_path_Error_Rows, Error_Row_Paths)

        if 'pyj0827' not in self.MailTo:
            self.MailTo.append('pyj0827')
        if not IS_DEBUG:
            if 'Joyang' not in self.MailTo:
                self.MailTo.append('Joyang')
            if 'khseo' not in self.MailTo: 
                self.MailTo.append('khseo')
            if 'ktpark' not in self.MailTo: 
                self.MailTo.append('ktpark')

        error_ratio = (len(err_file_list) / len(Target_file_list)) * 100

        MyEmaillib.Send_Report(self.MailTo, 
        '''
        Civil NS Post Table Regression Test Result
        Test Date : {0}
        Target Civil DLL Path : {1}
        Target Solver DLL Path : {2}
        Error Model File Percentage : {3}%({4}/{5})

        ---------------------------------------------------------------
        Regression Test Result Copy To : {6}
        ---------------------------------------------------------------

        '''. format(datetime.today().strftime('%Y-%m-%d'), self.Origin_Cvl_Path, self.Origin_Solver_Path, error_ratio, str(len(err_file_list)), str(len(Target_file_list)), self.Export_Share_Path),
        [self.Report_Path + ".xml", zip_path_Error_Files, zip_path_Error_Rows])
        return 

    def ExportToShareFolder(self, err_file_list:list[str], Error_Row_Paths:list[str] ):
        if os.path.isdir(self.Export_Share_Path):
            shutil.rmtree(self.Export_Share_Path)
        os.makedirs(self.Export_Share_Path)

        csv_path = os.path.join(self.Export_Path, "MEC_RESULT")

        for file_path in err_file_list:
            copy_to_path = os.path.join(self.Export_Share_Path, os.path.relpath(file_path, csv_path).replace('..\\', ''))
            if not os.path.isdir(os.path.dirname(copy_to_path)):
                os.makedirs(os.path.dirname(copy_to_path))
            copyfile(file_path, copy_to_path)
        
        for file_path in Error_Row_Paths:
            copy_to_path = os.path.join(self.Export_Share_Path, os.path.relpath(file_path, self.Export_Path).replace('..\\', ''))
            if not os.path.isdir(os.path.dirname(copy_to_path)):
                os.makedirs(os.path.dirname(copy_to_path))
            copyfile(file_path,copy_to_path )

        copy_to_path = os.path.join(self.Export_Share_Path, os.path.relpath(self.Report_Path, self.Export_Path).replace('..\\', ''))
        if not os.path.isdir(os.path.dirname(copy_to_path)):
            os.makedirs(os.path.dirname(copy_to_path))
        copyfile(self.Report_Path + ".xml", copy_to_path + ".xml")
        return 

if __name__ == "__main__":
    PostRT = GenCivilPostRT()

    if not PostRT.Initialize(sys.argv):
        PostRT.PrintDescription()
        sys.exit(-1)

    if not PostRT.Run():
        sys.exit(-1)

    sys.exit(0)