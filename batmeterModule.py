class batmeter_client:
    def __init__(self, id:str, loadmeter:object):
        self.id = self.__class__.__name__
        self.Batmeter_Cur = [0x05,0x03,0x00,0x05,0x00,0x02,0xD5,0x8E]
        self.Batmeter_Wat = [0x05,0x03,0x00,0x00,0x00,0x08,0x0C,0x44]
        self.RM = 40000000
        self.BatFCC = 6000000
        self.data_silo = {
            'BatCurSoc':0,
            'SOC':0,
        }
        self.loadmeter = loadmeter

    def init_data_silo(self,):
        self.data_silo = {
            'BatCurSoc':0,
            'SOC':0,
        }
    
    def get_outputVol(self,):
        return self.loadmeter.data_silo['outputVol']

    def ser_read(self, ser):
        try:
            ser.write(self.Batmeter_Cur)
            buf = ser.read(10)
            BatCur = int(buf[4] + (buf[3] << 8))
            if (BatCur > 50000):
                self.data_silo['BatCurSoc'] = BatCur-65536 
            else:
                self.data_silo['BatCurSoc'] = BatCur
            
            if (self.get_outputVol() >= 3297):
                if (self.data_silo['BatCurSoc'] < 10):
                    self.RM = 5994000
            self.RM = int(self.RM + self.data_silo['BatCurSoc'])
            self.data_silo['SOC'] = (self.RM/self.BatFCC) * 100
            if (self.data_silo['SOC'] >= 99.9):
                self.data_silo['SOC'] = 99.9
                self.RM = 5994000

        except Exception as e:
            self.init_data_silo()
            print(f'{self.__class__.__name__} ser_read error:' +  str(e))