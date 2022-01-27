class ExportOptFile:
    list_Opt = []
    Export_Path = ''
    Analysis_From = ''

    def __init__(self) -> None:
        self.list_Opt = ['RESULT']
        self.Export_Path = ''
        self.Analysis_From = ''
        return 

    def Initialize(self, Export_Path: str, Analysis_From:str, list_additional_Opt: list = []):
        self.Export_Path = Export_Path
        self.list_Opt += list_additional_Opt
        self.Analysis_From = Analysis_From

    def Export(self) -> str:
        f = open(self.Export_Path + '\\PostRT.csv', 'w')

        for Opt_String in self.list_Opt:
            f.write('OPT='+Opt_String+'\n')
        f.write('BINARY=ON\n')
        f.write('SRC='+self.Export_Path+'\\SRC\n')
        f.write('SRC='+self.Export_Path+'\\' + self.Analysis_From  +  '\\TGT\n')
        f.close()
        return 
    
if __name__ == "__main__":
    Exporter = ExportOptFile()
    Exporter.Initialize('D:\\MIDAS\\Post RT', 'MEC')
    Exporter.Export()
