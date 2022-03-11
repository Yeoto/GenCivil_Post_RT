from email.mime import base
import smtplib
from os.path import basename, splitext, isdir, isfile
from os import remove
from email.message import EmailMessage
from sys import argv
from turtle import bgcolor
import zipfile
import openpyxl
from openpyxl.styles import PatternFill
from pyparsing import col

class MyZiplib:
    def MakeZip(export_path:str, zip_file_list:list[str]) -> None:
        if isdir(export_path):
            remove(export_path)
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as file_zip:
            for file_path in zip_file_list:
                file_zip.write(file_path, arcname=basename(file_path))
            file_zip.close()

class MyEmaillib:
    def Send_Report(Mail_to:list[str], message:str, attachment:list[str]=[]) -> None:
        msg = EmailMessage()
        msg['Subject'] = 'Civil NS Post Table Regression Test Result !!'
        msg['From'] = 'pyj0827@midasit.com'

        mail_to_str = ''
        for id in Mail_to:
            if id.find('@') == -1:
                id += "@midasit.com"
            mail_to_str += id + ', '
        msg['To'] = mail_to_str[0:-2]

        msg.add_header('Content-Type', 'text')
        msg.set_payload(message)

        for file in attachment:
            with open(file, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype=splitext(file)[1],filename=basename(file))

        try:
            smtp = smtplib.SMTP_SSL('smtp.mailplug.co.kr', timeout=100)
            smtp.login('pyj0827@midasit.com', 'qkrdbwls00@@')
            smtp.send_message(msg)
            smtp.quit()
        except Exception as e:
            pass

class MyXLlib:
    __workbook = openpyxl.Workbook
    __line = 1
    __worksheet = object
    __SheetModified = bool

    def __init__(self) -> None:
        self.__workbook = openpyxl.Workbook()
        self.__line = 1
        return

    def CreateSheet(self, TableName: str) -> None:
        if self.__worksheet != None and self.__SheetModified == False:
            self.__workbook.remove(self.__worksheet)
        self.__SheetModified = False
        self.__line = 1
        self.__worksheet = self.__workbook.create_sheet(TableName)
        return

    def WriteLine(self, base_datas: list[(str, str)], tgt_datas: list[(str, str)] = []) -> None:
        if len(base_datas) == 0 and len(tgt_datas) == 0:
            self.__line += 1
            return
        
        if len(base_datas) == 0 and len(tgt_datas) > 0:
            base_datas = tgt_datas.copy()
            tgt_datas = []

        if len(tgt_datas) > 0:
            self.__worksheet.cell(row=self.__line, column=1).value = "FES"
            self.__SheetModified = True


        for i in range(len(base_datas)):
            cell_tuple = base_datas[i]
            cell = self.__worksheet.cell(row=self.__line, column=i + 2)
            cell.value = cell_tuple[0]

            if cell_tuple[1] == 'Failure':
                # 값 오류 = 빨간색
                cell.fill = PatternFill(start_color="FFC7CE", fill_type='solid')
            elif cell_tuple[1] == 'Error':
                # 타입 오류 = 노란색
                cell.fill = PatternFill(start_color="FFEB9C", fill_type='solid')
        self.__line += 1

        if len(tgt_datas) > 0:
            self.__worksheet.cell(row=self.__line, column=1).value = "MEC"

            for i in range(len(tgt_datas)):
                cell_tuple = tgt_datas[i]
                cell = self.__worksheet.cell(row=self.__line, column=i + 2)
                cell.value = cell_tuple[0]

                if cell_tuple[1] == 'Failure':
                    # 값 오류 = 빨간색
                    cell.fill = PatternFill(start_color="FFC7CE", fill_type='solid')
                elif cell_tuple[1] == 'Error':
                    # 타입 오류 = 노란색
                    cell.fill = PatternFill(start_color="FFEB9C", fill_type='solid')
        self.__line += 1

        return

    def save(self, path: str) -> None:
        if isfile(path):
            remove(path)

        if self.__worksheet != None and self.__SheetModified == False:
            self.__workbook.remove(self.__worksheet)
            
        if self.__workbook['Sheet'] != None:
            self.__workbook.remove(self.__workbook['Sheet'])

        self.__workbook.save(path)
        return 

if __name__ == "__main__":
    MyEmaillib.Send_Report(['pyj0827'], [argv[5], 'C:\\MIDAS\\MODEL\\POST RT\\MEC_RESULT.zip'])