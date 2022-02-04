#-*- coding: utf-8 -*-
from math import fabs
from os import path
import re
from junit_xml_custom import TestSuite, TestCase

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
    Tolerance = float
    Base_Table = {}
    Target_Table = {}

    def __init__(self, Tol:float) -> None:
        self.Tolerance = Tol
        return 

    def InitializeTableData(self, base_file_list, Tgt_file_list):
        self.Base_Table = self.Parse_TableData(base_file_list)
        self.Target_Table = self.Parse_TableData(Tgt_file_list)

    def GetValue(self, num):
        try:
            v = float(num)
            return v
        except ValueError:
            return num

    def RunDiff(self, report_path: str) -> bool:
        ts_list = []
        list_table_keys = list(self.Target_Table.keys())
        for File_Name in list_table_keys:
            print('{0}/{1} : {2}'.format(list_table_keys.index(File_Name), len(list_table_keys), File_Name))

            if File_Name not in self.Base_Table:
                continue

            LinePosSpan_Base = self.Base_Table[File_Name]
            LinePosSpan_Tgt = self.Target_Table[File_Name]

            Base_File_Path = LinePosSpan_Base[0]
            Tgt_File_Path = LinePosSpan_Tgt[0]

            tc_list = []
            for TableID, LineSpan_Tgt in LinePosSpan_Tgt[1].items():
                if TableID not in LinePosSpan_Base[1]:
                    continue
                
                tc = TestCase('Table Name : ' + str(LineSpan_Tgt[0]), allow_multiple_subelements=True)
                tc_list.append(tc)

                try:
                    LineSpan_Base = LinePosSpan_Base[1][TableID]

                    if (LineSpan_Base[1][1] - LineSpan_Base[1][0]) != (LineSpan_Tgt[1][1] - LineSpan_Tgt[1][0]):
                        raise DiffException('Error', '테이블 레코드의 갯수가 일치하지 않습니다')

                    with open(Base_File_Path, 'r') as f:
                        base_lines = f.readlines()[LineSpan_Base[1][0]:LineSpan_Base[1][1]]

                    with open(Tgt_File_Path, 'r') as f:
                        tgt_lines = f.readlines()[LineSpan_Tgt[1][0]:LineSpan_Tgt[1][1]]

                    for i in range(len(tgt_lines)):
                        base_line = base_lines[i]
                        tgt_line = tgt_lines[i]

                        base_datas = base_line.split(',')
                        tgt_datas = tgt_line.split(',')

                        if len(base_datas) != len(tgt_datas):
                            raise DiffException('Error', '테이블 레코드의 갯수가 일치하지 않습니다')

                        for j in range(len(tgt_datas)):
                            base_data = base_datas[j]
                            tgt_data = tgt_datas[j]

                            real_value_base = self.GetValue(base_data)
                            real_value_tgt = self.GetValue(tgt_data)

                            if type(real_value_base) != type(real_value_tgt):
                                tc.add_error_info('테이블 데이터의 타입이 일치하지 않습니다. 위치 : Col({0}) Row({1})'.format(j, i))
                                continue

                            IsSame = False
                            if type(real_value_tgt) == type(''):
                                IsSame = real_value_tgt == real_value_base
                            elif type(real_value_tgt) == type(0.0):
                                IsSame = fabs(real_value_tgt - real_value_base) < self.Tolerance

                            if IsSame == False:
                                tc.add_failure_info('테이블 데이터의 값이 일치하지 않습니다. 위치 : Col({0}) Row({1})'.format(j, i))

                except DiffException as e:
                    err_code = e.GetErrorCode()

                    if err_code == 'Failure':
                        tc.add_failure_info(e)
                    elif err_code == 'Error':
                        tc.add_error_info(e)

            ts = TestSuite('Post Table RT : ' + File_Name, tc_list)
            ts_list.append(ts)

        with open(report_path, 'w', encoding='utf-8') as f:
            TestSuite.to_file(f, ts_list, prettyprint=True, encoding='utf-8')
        return 

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