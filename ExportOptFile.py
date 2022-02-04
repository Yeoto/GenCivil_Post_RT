import os
import shutil
import glob

class ExportOptFile:
    list_Opt = []
    Export_Path = ''
    Analysis_From = ''

    #export_path
    Src_Path = ''
    Tgt_Path = ''
    FileFullPath = ''

    def __init__(self, Export_Path: str, Analysis_from: str, list_additional_Opt: list = []) -> None:
        self.list_Opt = ['RESULT']
        self.Export_Path = ''
        self.Analysis_From = ''
        self.Initialize(Export_Path, Analysis_from, list_additional_Opt)
        return 

    def Initialize(self, Export_Path: str, Analysis_From:str, list_additional_Opt: list = []):
        self.Export_Path = Export_Path
        self.list_Opt += list_additional_Opt
        self.Analysis_From = Analysis_From

    def GetPKID(self) -> str:
        license_path = glob.glob("\\\\midasitdev\\100_Dev\\Pub\\Midas Lock Number\\*라이선스.txt")[0]
        f_license = open(license_path, 'r')

        for line in f_license.readlines():
            if line.find('PKID') == -1:
                continue

            line = line.strip()
            return line[-16:]
        return ''

    def Export(self, Export_New_Data: bool = True) -> None:
        if not os.path.isdir(self.Export_Path):
            os.makedirs(self.Export_Path)
        
        self.FileFullPath = self.Export_Path + '\\' + self.Analysis_From + '_PostRT.csv'
        f = open(self.FileFullPath, 'w')

        PKID = self.GetPKID()
        f.write('PKID=' + PKID + '\n')

        for Opt_String in self.list_Opt:
            f.write('OPT='+Opt_String+'\n')
        f.write('BINARY=ON\n')

        self.Src_Path = (self.Export_Path+'\\MODEL')
        if Export_New_Data == True:
            if os.path.isdir(self.Src_Path):
                shutil.rmtree(self.Src_Path)
            os.makedirs(self.Src_Path)

        self.Tgt_Path = (self.Export_Path+ '\\' + self.Analysis_From + '_RESULT')
        if Export_New_Data == True:
            if os.path.isdir(self.Tgt_Path):
                shutil.rmtree(self.Tgt_Path)
            os.makedirs(self.Tgt_Path)
        
        f.write('SRC='+self.Src_Path +'\n')
        f.write('TGT='+self.Tgt_Path +'\n')
        f.close()
        return 
    
    def GetPath(self):
        return self.Src_Path, self.Tgt_Path, self.FileFullPath

if __name__ == "__main__":
    Exporter = ExportOptFile('C:\\MIDAS\\MODEL\\POST RT', 'MEC')
    Exporter.Export()

    print(Exporter.GetPath())
