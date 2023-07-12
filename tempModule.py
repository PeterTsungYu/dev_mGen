import time

class temp_client:
    def __init__(self, id:str,):
        self.id = self.__class__.__name__
        self.Temperature_Modbus = [0x04, 0x03,0x00,0x04,0x00,0x02,0x85,0x9F]
        self.data_silo = {
            'T1':0,
            'T2':0,
            'T3':0,
            'T4':0,
        }

    def init_data_silo(self,):
        self.data_silo = {
            'T1':0,
            'T2':0,
            'T3':0,
            'T4':0,
        }

    def ser_read(self, ser):
        try:
            ser.write(self.Temperature_Modbus)
            time.sleep(0.3)
            buf = ser.read(15)
            
            self.data_silo['T1'] = int(buf[4] + (buf[3] << 8))
            if (self.data_silo['T1'] > 50000):
                self.data_silo['T1'] = 250
            #print(T1)
            
            self.data_silo['T2'] = int(buf[6] + (buf[5] << 8))
            if (self.data_silo['T2'] > 50000):
                self.data_silo['T2'] = 250
            #print(T2)

            self.data_silo['T3'] = int(buf[8] + (buf[7] << 8))
            if (self.data_silo['T3'] > 50000):
                self.data_silo['T3'] = 250
            #print(T3)

            self.data_silo['T4'] = int(buf[10] + (buf[9] << 8))
            if (self.data_silo['T4'] > 50000):
                self.data_silo['T4'] = 250
            #print(T4)

        except Exception as e:
            self.init_data_silo()
            print(f'{self.__class__.__name__} ser_read error:' +  str(e))