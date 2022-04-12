import os
import shutil
import glob

class ExportOptFile:
    list_Opt = []
    Export_Path = ''
    Analysis_From = ''

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
        list_license_path = glob.glob("\\\\midasitdev\\100_Dev\\Pub\\Midas Lock Number\\*라이선스.txt")
        if len(list_license_path) == 0:
            return ''

        license_path = list_license_path[0]
        f_license = open(license_path, 'r')

        for line in f_license.readlines():
            if line.find('PKID') == -1:
                continue

            line = line.strip()
            return line[-16:]
        return ''

    def Export(self, Export_New_Data: bool = True, Additional_Folder: str = ''):
        if not os.path.isdir(self.Export_Path):
            os.makedirs(self.Export_Path)
        
        FileFullPath = self.Export_Path + '\\' + self.Analysis_From + '_PostRT.csv'
        f = open(FileFullPath, 'w')

        PKID = self.GetPKID()
        if PKID != '':
            f.write('PKID=' + PKID + '\n')

        for Opt_String in self.list_Opt:
            f.write('OPT='+Opt_String+'\n')
        f.write('BINARY=ON\n')

        Src_Path = os.path.join(self.Export_Path, self.Analysis_From+'_MODEL', Additional_Folder)
        if Export_New_Data == True:
            if os.path.isdir(Src_Path):
                shutil.rmtree(Src_Path)
            os.makedirs(Src_Path)

        Tgt_Path = os.path.join(self.Export_Path, self.Analysis_From+'_RESULT', Additional_Folder)
        if Export_New_Data == True:
            if os.path.isdir(Tgt_Path):
                shutil.rmtree(Tgt_Path)
            os.makedirs(Tgt_Path)
        
        f.write('SRC='+Src_Path +'\n')
        f.write('TGT='+Tgt_Path +'\n')
        f.close()
        return Src_Path, Tgt_Path, FileFullPath
    
    def GetPath(self):
        return self.Src_Path, self.Tgt_Path, self.FileFullPath

if __name__ == "__main__":
    Exporter = ExportOptFile('C:\\MIDAS\\MODEL\\POST RT', 'MEC')
    Exporter.Export()

    print(Exporter.GetPath())
