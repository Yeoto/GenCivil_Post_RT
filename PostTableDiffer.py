#-*- coding: utf-8 -*-
from math import fabs
from os import path, cpu_count
import re
from junit_xml_custom import TestSuite, TestCase
from MyUtils import MyXLlib
from multiprocessing import Pool

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
    ts_list = []

    def __init__(self, Val_Tol:float, Per_Tol:float) -> None:
        self.Val_Tolerance = Val_Tol
        self.Per_Tolerance = Per_Tol
        return 

    def InitializeTableData(self, base_file_list, Tgt_file_list):
        self.Base_Table = self.Parse_TableData(base_file_list)
        self.Target_Table = self.Parse_TableData(Tgt_file_list)

    def Parse_TableData(self, file_list):
        LinePosDict = {}
        for file_path in file_list:
            LinePosList = {}
            curTableID = 0
            curTableName = ''
            LinePosStart = (0, 0)

            p = re.compile(r'\( #DS_ID : (\d+) \) (.+)')
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for i in range(len(lines)):
                    line = lines[i]
                    if line[0:5] != '( #DS':
                        continue

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

    def GetValue(num):
        try:
            v = float(num)
            return v
        except ValueError:
            if type(num) == type(''):
                return num.strip()
            return num

    def RunDiff_Line(self, index: int, base_line: str, tgt_line: str):
        base_datas = base_line.strip().split(',')
        tgt_datas = tgt_line.strip().split(',')

        TypeErrorSet = set()
        ValueErrorSet = set()

        if len(base_datas) != len(tgt_datas):
            return (index, TypeErrorSet, ValueErrorSet)

        excel_datas = list(tuple())
        for j in range(len(tgt_datas)):
            base_data = base_datas[j].strip()
            tgt_data = tgt_datas[j].strip()

            real_value_base = PostTableDiffer.GetValue(base_data)
            real_value_tgt = PostTableDiffer.GetValue(tgt_data)

            if type(real_value_base) != type(real_value_tgt):
                TypeErrorSet.add(j)
                excel_datas.append((base_data, tgt_data, 'Error'))
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
                ValueErrorSet.add(j)
                excel_datas.append((base_data, tgt_data, 'Failure'))
                continue

            excel_datas.append((base_data, tgt_data, ''))

        IsErrorRow = (len(TypeErrorSet) + len(ValueErrorSet)) > 0

        if IsErrorRow == False:
            return (index, TypeErrorSet, ValueErrorSet)

        return (index, TypeErrorSet, ValueErrorSet)

    def RunDiff(self, error_row_path: str, Export_All_Err:bool = False, IS_DEBUG: bool = False) -> list[str]:
        def ThrowError(tc:TestCase, err_code:str, msg:str, err_file_list:list, file_path:str):
            if err_code == 'Failure':
                tc.add_failure_info(msg)
            elif err_code == 'Error':
                tc.add_error_info(msg)

            if file_path not in err_file_list:
                err_file_list.append(file_path)
        
        diff_sheet = MyXLlib()

        err_file_list = []
        list_table_keys = list(self.Target_Table.keys())
        for File_Name in list_table_keys:
            if IS_DEBUG == True:
                print('{0}/{1} : {2}'.format(list_table_keys.index(File_Name) + 1, len(list_table_keys), File_Name))

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

                if LineSpan_Base[1][1] - LineSpan_Base[1][0] < 1 or LineSpan_Tgt[1][1] - LineSpan_Tgt[1][0] < 1:
                    continue

                with open(Base_File_Path, 'r') as f:
                    base_lines = f.readlines()[LineSpan_Base[1][0]:LineSpan_Base[1][1]]

                with open(Tgt_File_Path, 'r') as f:
                    tgt_lines = f.readlines()[LineSpan_Tgt[1][0]:LineSpan_Tgt[1][1]]

                L = list[(int, set, set)]
                if len(tgt_lines) > 100000:
                    with Pool(processes=cpu_count()*2) as p:
                        L = p.starmap(self.RunDiff_Line, [(i, base_lines[i], tgt_lines[i]) for i in range(1,len(tgt_lines))])
                else:
                    L = []
                    for i in range(1, len(tgt_lines)):
                        L.append(self.RunDiff_Line(i, base_lines[i], tgt_lines[i]))

                L.sort(key=lambda index: index[0])
                result_data = {i:(TypeErr, ValueErr) for i, TypeErr, ValueErr in L if len(TypeErr) > 0 or len(ValueErr) > 0}

                if len(result_data) > 0:
                    diff_sheet.WriteLine([File_Name + ': ' + LineSpan_Tgt[0]], col_offset=0)
                    diff_sheet.WriteLine([f.strip() for f in tgt_lines[0].strip().split(',')])

                    index_list = []
                    if len(result_data) > 100 and Export_All_Err == False:
                        index_list = list(result_data.keys())[:50] + list(result_data.keys())[len(result_data.keys()) - 50:]
                    else:
                        index_list = list(result_data.keys())

                    for i in index_list:
                        if len(result_data) > 100 and index_list.index(i) == 50:
                            diff_sheet.WriteLine(['Error Too Much. {0} Rows Hided'.format(len(tgt_lines) - 100)])
                            diff_sheet.WriteLine([])

                        base_datas = base_lines[i].strip().split(',')
                        tgt_datas = tgt_lines[i].strip().split(',')

                        excel_data = [(base_datas[j], tgt_datas[j], 'Failure' if j in result_data[i][1] else 'Error' if j in result_data[i][0] else '') for j in range(len(tgt_datas))]

                        diff_sheet.WriteDualLine(excel_data)
                        diff_sheet.WriteLine([])

                    diff_sheet.WriteLine([])
                    diff_sheet.WriteLine([])

                    TypeErrorCnt = sum([len(result_data[idx][0]) for idx in result_data.keys()])
                    ValueErrorCnt = sum([len(result_data[idx][1]) for idx in result_data.keys()])

                    if ValueErrorCnt > 0:
                        ThrowError(tc, 'Failure', 'Value Error {0}개'.format(ValueErrorCnt), err_file_list, Tgt_File_Path)
                    if TypeErrorCnt > 0:
                        ThrowError(tc, 'Error', 'Type Error {0}개'.format(TypeErrorCnt), err_file_list, Tgt_File_Path)

            ts = TestSuite('Post Table RT : ' + File_Name, tc_list)
            self.ts_list.append(ts)

        diff_sheet.save(error_row_path)

        return err_file_list

    def SaveJunit(self, report_path:str):
        with open(report_path, 'w', encoding='utf-8') as f:
            TestSuite.to_file(f, self.ts_list, prettyprint=False, encoding='utf-8')
        
if __name__ == "__main__":
    pass