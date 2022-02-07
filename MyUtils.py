import smtplib
from os.path import basename, splitext, isdir
from os import remove
from email.message import EmailMessage
from sys import argv
import zipfile

class MyZiplib:
    def MakeZip(export_path:str, zip_file_list:list[str]) -> None:
        if isdir(export_path):
            remove(export_path)
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as file_zip:
            for file_path in zip_file_list:
                file_zip.write(file_path, arcname=basename(file_path))
            file_zip.close()

class MyEmaillib:
    def Send_Report(Mail_to:list[str], attachment:list[str]=[]) -> None:
        msg = EmailMessage()
        msg['Subject'] = 'Civil NS Post Table Regression Test Result !!'
        msg['From'] = 'pyj0827@midasit.com'
        msg['To'] = ', '.join([f+"@midasit.com" for f in Mail_to])
        msg.add_header('Content-Type', 'text')
        msg.set_payload('Asdf Asdf Asdf')

        for file in attachment:
            with open(file, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype=splitext(file)[1],filename=basename(file))

        try:
            smtp = smtplib.SMTP_SSL('smtp.mailplug.co.kr', timeout=100)
        except Exception as e:
            pass

        smtp.login('pyj0827@midasit.com', 'qkrdbwls00@@')
        smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
        smtp.quit()

if __name__ == "__main__":
    MyEmaillib.Send_Report(['pyj0827'], [argv[5], 'C:\\MIDAS\\MODEL\\POST RT\\MEC_RESULT.zip'])