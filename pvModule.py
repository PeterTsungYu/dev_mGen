import time

class pv_client:
    def __init__(self, id:str,):
        self.id = self.__class__.__name__
        self.PV_modbus = [0x04, 0x03,0x00,0x04,0x00,0x02,0x85,0x9F]
        self.data_silo = {
            'PV1V':0,
            'PV1A':0,
            'PV2V':0,
            'PV2A':0,
            'PVT':0,
        }

    def init_data_silo(self,):
        self.data_silo = {
            'PV1V':0,
            'PV1A':0,
            'PV2V':0,
            'PV2A':0,
            'PVT':0,
        }

    def ser_read(self, ser):
        try:
            ser.write(self.PV_modbus)
            time.sleep(0.3)
            buf = ser.read(17)
            self.data_silo['PV1V'] = int(buf[4] + (buf[3] << 8))
            self.data_silo['PV1A'] = float(buf[6] + (buf[5] << 8))*0.1
            self.data_silo['PV2V'] = int(buf[8] + (buf[7] << 8))
            self.data_silo['PV2A'] = float(buf[10] + (buf[9] << 8))*0.1
            self.data_silo['PVT'] = int(buf[12] + (buf[11] << 8))

        except Exception as e:
            self.init_data_silo()
            print(f'{self.__class__.__name__} ser_read error:' +  str(e))
        
        