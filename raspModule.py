import RPi.GPIO as GPIO
import serial
import board
import busio
import time
import threading

class rpi_server:
    def __init__(self, id:str, lst_clients:list):
        self.id = self.__class__.__name__
        self.lst_clients = lst_clients
        self.fuelPumpControl = 17
        self.powerRelayControl = 27
        self.batDry = 22
        self.leak = 23
        self.tach = 24
        self.overFlowDry = 25
        self.fan_Pin = 18
        self.pwm_freq = 25000
        self.gpio_setup()
        self.fan = self.fan_setup()
        self.ser = self.ser_setup()
        self.i2c = self.i2c_setup()
        self.client_threads = []
        self.thread_timeout = 10
        self.stop_threads = False
        self.data_silo = {}

    def gpio_setup(self,):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.tach, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Pull up to 3.3V
        GPIO.setup(self.fan_Pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.leak, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)# pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.overFlowDry, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.batDry, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.fuelPumpControl, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.powerRelayControl, GPIO.OUT, initial=GPIO.LOW)

    def fan_setup(self,):
        fan = GPIO.PWM(self.fan_Pin, self.pwm_freq)
        fan.start(80)
        return fan

    def ser_setup(self,):
        try:
            ser = serial.Serial()
            ser.port = "/dev/ttyUSB0"
            ser.baudrate = 9600
            ser.bytesize = serial.EIGHTBITS
            ser.parity = serial.PARITY_NONE
            ser.stopbits = serial.STOPBITS_ONE
            ser.timeout = 0.1
            ser.writeTimeout = 0.1
            ser.xonxoff = False
            ser.rtscts = False
            ser.dsrdtr = False
            ser.open()
        except Exception as e:
            ser = None
            print(f'{self.__class__.__name__} ser_setup error:' +  str(e))
        return ser
    
    def i2c_setup(self,):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
        except Exception as e:
            i2c = None
            print(f'{self.__class__.__name__} ads_setup error:' +  str(e))
        return i2c

    def init_data_silo(self,):
        self.data_silo = {}

    def ser_get_client_data(self,):
        if isinstance(self.ser, serial.serialposix.Serial):
            while not self.stop_threads:
                for client in self.lst_clients:
                    if hasattr(client, 'ser_read'):
                        client.ser_read(self.ser)
                time.sleep(self.threading_timeout)
        else:
            pass
    
    def i2c_get_client_data(self,):
        if self.i2c:
            while not self.stop_threads:
                for client in self.lst_clients:
                    if hasattr(client, 'i2c_read'):
                        client.i2c_read(self.ser)
                time.sleep(self.threading_timeout)
        else:
            pass
    
    def collect_client_data_silos(self,):
        while not self.stop_threads:
            try:
                self.init_data_silo()
                for client in self.lst_clients:
                    self.data_silo[client.id] = client.data_silo
                time.sleep(self.threading_timeout)
            except Exception as e:
                self.init_data_silo()
                print(f'{self.__class__.__name__} collect_client_data_silos error:' +  str(e))
            time.sleep(self.threading_timeout)
    
    def start_client_threads(self,):
        thread = threading.Thread(target=self.ser_get_client_data, name=f'{self.id}_ser_get_client_data',)
        thread.start()
        self.client_threads.append(thread)

        thread = threading.Thread(target=self.i2c_get_client_data, name=f'{self.id}_i2c_get_client_data',)
        thread.start()
        self.client_threads.append(thread)

        thread = threading.Thread(target=self.collect_client_data_silos, name=f'{self.id}_collect_client_data_silos',)
        thread.start()
        self.client_threads.append(thread)

    def stop_client_threads(self,):
        self.stop_threads = True
        # Close all client sockets
        for client_thread in self.client_threads:
            client_thread.join()
        self.client_threads = []
