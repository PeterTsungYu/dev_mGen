import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class fuelLevel_client:
    def __init__(self, id:str,):
        self.id = self.__class__.__name__
        self.data_silo = {
            'FuelLevel':0,
        }

    def init_data_silo(self,):
        self.data_silo = {
            'FuelLevel':0,
        }

    def i2c_read(self, i2c):
        try:
            ads = ADS.ADS1015(i2c)
            fuelLevel = AnalogIn(ads, ADS.P0)
            self.data_silo['FuelLevel'] = ((fuelLevel.voltage-3.44)/(1.48-3.44))*100
            if (self.data_silo['FuelLevel'] <= 0):
                self.data_silo['FuelLevel'] = 0
            elif (self.data_silo['FuelLevel'] >= 100):
                self.data_silo['FuelLevel'] = 100

        except Exception as e:
            self.init_data_silo()
            print(f'{self.__class__.__name__} i2c_read error:' +  str(e))
        
        