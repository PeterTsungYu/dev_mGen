class loadmeter_client:
    def __init__(self, id:str,):
        self.id = self.__class__.__name__
        self.Loadmeter_Vol = [0x04, 0x03,0x00,0x04,0x00,0x02,0x85,0x9F]
        self.Loadmeter_Cur = [0x04, 0x03,0x00,0x05,0x00,0x02,0xD4,0x5F]
        self.Loadmeter_Wat = [0x04, 0x03,0x00,0x02,0x00,0x02,0x65,0x9E]
        self.data_silo = {
            'outputVol':0,
            'outputCur':0,
            'outputWat':0,
        }

    def init_data_silo(self,):
        self.data_silo = {
            'outputVol':0,
            'outputCur':0,
            'outputWat':0,
        }

    def ser_read(self, ser):
        try:
            ser.write(self.Loadmeter_Vol)
            buf = ser.read(10)
            self.data_silo['outputVol'] = buf[4] + (buf[3] << 8)
            
            ser.write(self.Loadmeter_Vol)
            buf = ser.read(10)
            self.data_silo['outputCur'] = (buf[4] + (buf[3] << 8))
            if (self.data_silo['outputCur'] > 10000):
                self.data_silo['outputCur'] = (self.data_silo['outputCur']-65536)
            
            ser.write(self.Loadmeter_Wat)
            buf = ser.read(10)
            self.data_silo['outputWat'] = buf[6] + (buf[5] << 8)
            if (self.data_silo['outputWat'] > 24000):
                self.data_silo['outputWat'] = self.data_silo['outputWat']-65536

        except Exception as e:
            self.init_data_silo()
            print(f'{self.__class__.__name__} ser_read error:' +  str(e))