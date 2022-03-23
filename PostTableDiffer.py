#-*- coding: utf-8 -*-
from math import fabs
from os import path, remove
import re
from junit_xml_custom import TestSuite, TestCase
from MyUtils import MyXLlib

class DiffException(Exception):
    Error_Code = str
    msg = str

    def __init__(self, Error_Code:str, msg:str) -> None:
        self.Error_Code = Error_Code
        self.msg = msg

    def __str__(self):
        return "Regression Test " + self.Error_Code + " : " + self.msg

    def GetErrorCode(self):
        return self.Error_Code

class PostTableDiffer:
    Val_Tolerance = float
    Per_Tolerance = float
    Base_Table = {}
    Target_Table = {}

    def __init__(self, Val_Tol:float, Per_Tol:float) -> None:
        self.Val_Tolerance = Val_Tol
        self.Per_Tolerance = Per_Tol
        return 

    def InitializeTableData(self, base_file_list, Tgt_file_list):
        self.Base_Table = self.Parse_TableData(base_file_list)
        self.Target_Table = self.Parse_TableData(Tgt_file_list)

    def GetValue(self, num):
        try:
            v = float(num)
            return v
        except ValueError:
            if type(num) == type(''):
                return num.strip()
            return num

    def RunDiff(self, report_path: str, error_row_path: str) -> list[str]:
        def ThrowError(tc:TestCase, err_code:str, msg:str, err_file_list:list, file_path:str):
            if err_code == 'Failure':
                tc.add_failure_info(msg)
            elif err_code == 'Error':
                tc.add_error_info(msg)

            if file_path not in err_file_list:
                err_file_list.append(file_path)
        
        diff_sheet = MyXLlib()

        ts_list = []
        err_file_list = []
        list_table_keys = list(self.Target_Table.keys())
        for File_Name in list_table_keys:
            print('{0}/{1} : {2}'.format(list_table_keys.index(File_Name), len(list_table_keys), File_Name))

            if File_Name not in self.Base_Table:
                continue

            LinePosSpan_Base = self.Base_Table[File_Name]
            LinePosSpan_Tgt = self.Target_Table[File_Name]

            Base_File_Path = LinePosSpan_Base[0]
            Tgt_File_Path = LinePosSpan_Tgt[0]

            diff_sheet.CreateSheet(File_Name)

            tc_list = []
            for TableID, LineSpan_Tgt in LinePosSpan_Tgt[1].items():
                if TableID not in LinePosSpan_Base[1]:
                    continue
                
                tc = TestCase('Table Name : ' + str(LineSpan_Tgt[0]), allow_multiple_subelements=True)
                tc_list.append(tc)

                LineSpan_Base = LinePosSpan_Base[1][TableID]

                if (LineSpan_Base[1][1] - LineSpan_Base[1][0]) != (LineSpan_Tgt[1][1] - LineSpan_Tgt[1][0]):
                    ThrowError(tc, 'Error', 'Row Count Diff.', err_file_list, Tgt_File_Path)
                    continue

                with open(Base_File_Path, 'r') as f:
                    base_lines = f.readlines()[LineSpan_Base[1][0]:LineSpan_Base[1][1]]

                with open(Tgt_File_Path, 'r') as f:
                    tgt_lines = f.readlines()[LineSpan_Tgt[1][0]:LineSpan_Tgt[1][1]]

                ErrorRowList = list(tuple())

                for i in range(1, len(tgt_lines)):
                    base_line = base_lines[i]
                    tgt_line = tgt_lines[i]

                    base_datas = base_line.split(',')
                    tgt_datas = tgt_line.split(',')

                    if len(base_datas) != len(tgt_datas):
                        ThrowError(tc, 'Error', 'Column Count Diff.', err_file_list, Tgt_File_Path)
                        break

                    TypeErrorSet = set()
                    ValueErrorSet = set()

                    for j in range(len(tgt_datas)):
                        base_data = base_datas[j]
                        tgt_data = tgt_datas[j]

                        real_value_base = self.GetValue(base_data)
                        real_value_tgt = self.GetValue(tgt_data)

                        if type(real_value_base) != type(real_value_tgt):
                            #ThrowError(tc, 'Error', 'Type Diff. Pos : Col({0}) Row({1})'.format(j, i), err_file_list, Tgt_File_Path)
                            TypeErrorSet.add(j)
                            continue

                        IsSame = False
                        if type(real_value_tgt) == type(''):
                            IsSame = real_value_tgt == real_value_base
                        elif type(real_value_tgt) == type(0.0):
                            if real_value_tgt == 0.0 or real_value_base == 0.0:
                                IsSame = fabs(real_value_tgt - real_value_base) < self.Val_Tolerance
                            else:
                                IsSame = fabs((real_value_tgt - real_value_base) / real_value_tgt) < ( self.Per_Tolerance / 100 )

                        if IsSame == False:
                            #ThrowError(tc, 'Failure', 'Value DIff. Pos : Col({0}) Row({1}). Value: Base "{2}" vs Tgt "{3}"'.format(j, i, real_value_base, real_value_tgt), err_file_list, Tgt_File_Path)
                            ValueErrorSet.add(j)
                            continue

                    ErrorRowList.append((TypeErrorSet, ValueErrorSet))
                
                printError = sum([len(f[0]) + len(f[1]) for f in ErrorRowList]) > 0
                if printError == True:
                    diff_sheet.WriteLine([(File_Name + ': ' + LineSpan_Tgt[0], '')], col_offset=0)
                    diff_sheet.WriteLine([(f.strip(),'') for f in tgt_lines[0].strip().split(',')])

                ValueErrorCnt = 0
                TypeErrorCnt = 0
                for j in range(len(ErrorRowList)):
                    TypeErrorSet = ErrorRowList[j][0]
                    ValueErrorSet = ErrorRowList[j][1]

                    ValueErrorCnt += len(ValueErrorSet)
                    TypeErrorCnt += len(TypeErrorSet)

                    if len(ValueErrorSet) > 0 or len(TypeErrorSet) > 0:
                        base_datas = list(tuple())
                        tgt_datas = list(tuple())

                        data_idx = 0
                        for base_data in base_lines[j + 1].split(','):
                            base_data = base_data.strip()
                            if data_idx in ValueErrorSet:
                                base_datas.append((base_data, 'Failure'))
                            elif data_idx in TypeErrorSet:
                                base_datas.append((base_data, 'Error'))
                            else:
                                base_datas.append((base_data, ''))

                            data_idx += 1

                        data_idx = 0
                        for tgt_data in tgt_lines[j + 1].split(','):
                            tgt_data = tgt_data.strip()
                            if data_idx in ValueErrorSet:
                                tgt_datas.append((tgt_data, 'Failure'))
                            elif data_idx in TypeErrorSet:
                                tgt_datas.append((tgt_data, 'Error'))
                            else:
                                tgt_datas.append((tgt_data, ''))

                            data_idx += 1

                        diff_sheet.WriteLine(base_datas, tgt_datas)
                        diff_sheet.WriteLine([])

                if printError == True:
                    diff_sheet.WriteLine([])
                    diff_sheet.WriteLine([])

                if ValueErrorCnt > 0:
                    ThrowError(tc, 'Failure', '값 오류 {0}개'.format(ValueErrorCnt), err_file_list, Tgt_File_Path)
                if TypeErrorCnt > 0:
                    ThrowError(tc, 'Error', '타입 오류 {0}개'.format(TypeErrorCnt), err_file_list, Tgt_File_Path)
                    
            ts = TestSuite('Post Table RT : ' + File_Name, tc_list)
            ts_list.append(ts)

        with open(report_path, 'w', encoding='utf-8') as f:
            TestSuite.to_file(f, ts_list, prettyprint=True, encoding='utf-8')

        diff_sheet.save(error_row_path)

        return err_file_list

    def Parse_TableData(self, file_list):
        LinePosDict = {}
        for file_path in file_list:
            file = open(file_path, 'r')

            LinePosList = {}
            curTableID = 0
            curTableName = ''
            LinePosStart = (0, 0)

            lines = file.readlines()
            for i in range(len(lines)):
                line = lines[i]
                p = re.compile(r'\( #DS_ID : (\d+) \) (.+)')
                m = p.match(line)
                if m == None:
                    continue

                if LinePosStart != 0 and curTableID != 0:
                    LinePosList[curTableID] = (curTableName, (LinePosStart, i - 1))

                curTableID = int(m.group(1))
                curTableName = m.group(2)
                LinePosStart = i + 2
                i+=1

            LinePosDict[path.splitext(path.basename(file_path))[0]] = (file_path, LinePosList)

        return LinePosDict

        
if __name__ == "__main__":
    pass