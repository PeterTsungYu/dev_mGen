import os
import sys
import ssl
import time
import json
import board
import busio
import signal
import socket
import struct
import serial
import smtplib
import hashlib
import requests
import sqlite3
import RPi.GPIO as GPIO
from email import encoders
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from email.mime.multipart import MIMEMultipart

SystemID = 13101
dataLasTI = 0
SendGmailTi = 0
SysRunTimeStart = time.time()
SysRunTimeStop = time.time()
SPECTI = time.time()
SetCMDTi = 0
StartTi = 0
LastTi = 0
SocTI = 0
EndTi = 0
SetCMD = 0
RM = 40000000
BatFCC = 6000000


fuelConsume = 0
UpdateDate = 0
sysAuto = 0
sysOutPut = 0
OutputVol = 500
T1 = 250
T2 = 250
rpm = 0
FCset = 2
FCcon = 0
step = 0
WAIT_TIME = 1           # 每次控制的更新頻率，單位為秒
PWM_FREQ = 25000        # PWM 頻率
t = time.time()
H3DataList = []
DeviceKey = '921f0bcd727783e6aa9363a534d65c66b7218671e988be31cf352470833c8a8f'
#-------------------------------------------------------------
#-----------------GPIO Setting--------------------------------
FuelPumControl = 17                                                         # 3.3V DO
PowerRelayControl = 27                                                      # 3.3V DO
BatDry = 22                                                                 # 3.3V DI
Leak = 23                                                                   # 3.3V DI
TACH = 24       # Fan's tachometer output pin                               # ??DI
OverFolwDry = 25                                                            # 3.3V DI
FAN_PIN = 18            # PWM 控制腳位，設定成你想接的位置即可，注意是 BCM 編號 # PWM
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(TACH, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Pull up to 3.3V
GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Leak, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)# pull_up_down=GPIO.PUD_UP)
GPIO.setup(OverFolwDry, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BatDry, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(FuelPumControl, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(PowerRelayControl, GPIO.OUT, initial=GPIO.LOW)
fan = GPIO.PWM(FAN_PIN,PWM_FREQ)
#--------------------------------------------------------------
PULSE = 2       # Noctua fans puts out two pluses per revolution           
PV1V = 0
PV1A = 0
PV2V = 0
PV2A = 0
PVT = 0
#-----------------http Config----------------------------------
url = 'http://upraw.hipower.ltd:9999/recv?v=1'
#-----------------i2c Config----------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1015(i2c)
fuelLevel = AnalogIn(ads, ADS.P0)
#---------------------------------------------------------------
#-----------------SerialPort Command---------------------------
Loadmeter_Vol = [0x04, 0x03,0x00,0x04,0x00,0x02,0x85,0x9F]
Loadmeter_Cur = [0x04, 0x03,0x00,0x05,0x00,0x02,0xD4,0x5F]
Loadmeter_Wat= [0x04, 0x03,0x00,0x02,0x00,0x02,0x65,0x9E]
Batmeter_Cur = [0x05,0x03,0x00,0x05,0x00,0x02,0xD5,0x8E]
Batmeter_Wat = [0x05,0x03,0x00,0x00,0x00,0x08,0x0C,0x44]
Temperature = [0x02,0x03,0x00,0x02,0x00,0x04,0xE5,0xFA]
PV = [0x03,0x03,0x00,0x00,0x00,0x06,0xC4,0x2A]
Arduino = [0x06,0x03,0x00,0x05,0x00,0x02,0xD5,0xBD]
#ARM = [0x01,0x03,0x00,0xFF,0x00,0xFF,0x35,0xBA]
#-----------------SerialPort Config for mGen PCB---------------------------
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
#-------------------------------------------------------------------
def FANcontrol(speed):
    fan.start(speed)
    return
def handleFANspeed():  #風速控制
    ser.write(Temperature)
    time.sleep(0.1)
    buf = ser.read(15)
    for i in range(len(buf)):
        break
    T1 = (buf[4] + (buf[3] << 8))*0.1
    if (T1 > 50000):
        T1 = 25
    #print(T1)
    T2 = (buf[6] + (buf[5] << 8))*0.1
    if (T2 > 50000):
        T2 = 25
    #print(T2)
    T3 = buf[8] + ((buf[7] << 8))*0.1
    if (T3 > 50000):
        T3 = 25
    #print(T3)
    T4 = buf[10] + ((buf[9] << 8))*0.1
    if (T4 > 50000):
        T4 = 25
    #print(T4)
    if T4 < 30:
        FANcontrol(10)
    elif T4 > 60:
        FANcontrol(50)
    #else:
     #   step = (80-10)/(60-30)
     #   T4 -= 20
     #   FANcontrol(10 + (round(T4) * step))
    return()
def fell(n):
    global t
    global rpm
    dt = time.time() - t
    if dt < 0.005:return
    frep = 1 /dt
    rpm = (frep / PULSE) * 60
    t = time.time()
        
def internet_on():
    try:    #若Internet 可以上網，則執行此
        socket.setdefaulttimeout(5)
        host = socket.gethostbyname("www.google.com")
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except Exception as e: #若Internet 無法上網，則執行此
        time.sleep(10)
        print('Internet error')
        return False
def hash_string(string):
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

def on_connect(client,userdata,flags,rc):
    if rc == 0:
        print('connected OK')
        client.subscribe('hiPowerMQTT/remoteCtrl/M101/cmd')
    else:
        print('Bad connection returned code=',rc)
def on_message(client,userdata,msg):
    MQTTcmd = msg.payload
    print(MQTTcmd)
    global UpdateDate,RemoteCmd,Value,sysuAuto,sysOutPut
    global Module1_Request_start,Module1_Request_stop,Module1_Request_reset,module1_CurSet,Module1_Enable,module1_State
    #global Module2_Request_start,Module2_Request_stop,Module2_Request_reset,module2_CurSet,Module2_Enable,module2_State
    global Module3_Request_start,Module3_Request_stop,Module3_Request_reset,module3_CurSet,Module3_Enable,module3_State
    data = json.loads(MQTTcmd)
    mqttCID = data['mqttCID']
    msg = data['msg']
    RemoteCmd = msg[0:msg.find('|')].strip('|')
    CMDstr = msg[msg.find('|'):len(msg)].strip('|')
    FCcont = int(CMDstr[0:CMDstr.find(':')].strip(':'))
    RemoteValue = CMDstr[CMDstr.find(':'):CMDstr.find('|')].strip(':')
    Value = '%s:%s'%(FCcont,RemoteValue)
    SHA256come = CMDstr[CMDstr.find('|'):len(CMDstr)].strip('|')
    ti = data['ti']
    SHA256Cal = '%s|%s|%s|%s|%s'%('M101',DeviceKey,ti,RemoteCmd,Value)
    if (SHA256come == hash_string(SHA256Cal)):
        RemoteCMD = 1
    # Manual control on website
    if (RemoteCMD == 1):
        print("Hi")
        print(RemoteCmd)
        print(FCcont)
        print(RemoteValue)
        if(RemoteCmd == 'FC_Control_Current_'):
            if(FCcont == 1):
                module1_CurSet = int(RemoteValue)
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=1-1")
                RemoteCMD = 0
                """
            elif(FCcont == 2):
                module2_CurSet = int(RemoteValue)
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                RemoteCMD = 0
            """
            elif(FCcont == 3):
                module3_CurSet = int(RemoteValue)
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=1-3")
                RemoteCMD = 0
            
        elif(RemoteCmd == 'FC_Control_Start_'):
            if(FCcont == 1):
                if (RemoteValue == '3'):
                    Module1_Request_start = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=2-1")
                RemoteCMD = 0
                """
            elif(FCcont == 2):
                if (RemoteValue == '3'):
                    Module2_Request_start = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                RemoteCMD = 0
            """
            elif(FCcont == 3):
                if (RemoteValue == '3'):
                    Module3_Request_start = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=2-3")
                RemoteCMD = 0
            
        elif(RemoteCmd == 'FC_Control_Stop_'):
            if(FCcont == 1):
                if (RemoteValue == '3'):
                    Module1_Request_stop = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=3-1")
                RemoteCMD = 0
                """
            elif(FCcont == 2):
                if (RemoteValue == '3'):
                    Module2_Request_stop = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                RemoteCMD = 0
            """    
            elif(FCcont == 3):
                if (RemoteValue == '3'):
                    Module3_Request_stop = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=3-3")
                RemoteCMD = 0
        elif(RemoteCmd == 'FC_Control_Reset_'):
            if(FCcont == 1):
                if (RemoteValue == '3'):
                    Module1_Request_reset = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=4-1")
                RemoteCMD = 0
                """
            elif(FCcont == 2):
                if (RemoteValue == '3'):
                    Module2_Request_reset = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                RemoteCMD = 0
            """
            elif(FCcont == 3):
                if (RemoteValue == '3'):
                    Module3_Request_reset = '01'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=4-3")
                RemoteCMD = 0
        elif(RemoteCmd == 'FC_Control_Enable_'):
            if(FCcont == 1):
                if (RemoteValue == '2'):
                    Module1_Enable = '01'
                elif(RemoteValue == '1'):
                    Module1_Enable = '00'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=5-1")
                RemoteCMD = 0
                
                """
            elif(FCcont == 2):
                if (RemoteValue == '2'):
                    Module2_Enable = '01'
                elif(RemoteValue == '1'):
                    Module2_Enable = '00'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                RemoteCMD = 0
            """
            elif(FCcont == 3):
                if (RemoteValue == '2'):
                    Module3_Enable = '01'
                elif(RemoteValue == '1'):
                    Module3_Enable = '00'
                time.sleep(1.5)
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                UpdateDate = 1
                print("FCcont=5-3")
                RemoteCMD = 0
        elif(RemoteCmd == 'SYS_Control_Power_'):
            if(FCcont == 0):
                sysuAuto = FCcont
                sysOutPut = RemoteValue
            
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                time.sleep(1.5)
                UpdateDate = 1
                print("FCcont=6-1")
                RemoteCMD = 0
            elif(FCcont == 1):
                sysuAuto = FCcont
                sysOutPut = RemoteValue
            
                client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('1','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
                time.sleep(1.5)                                                                           
                UpdateDate = 1
                print("FCcont=6-3")
                RemoteCMD = 0
        else:
            client.publish('hiPowerMQTT/remoteCtrl/M101/devFB',payload=json.dumps({'mqttCID':'M101_remotemqtt','msg':'%s|%s|%s|%s|%s'%('4','',ti,RemoteCmd,Value),'ti':int(inTI * 1000),
                                                                                       'rcFrom':mqttCID}))
#-----------------MQTT Config---------------------------------
broker = 'upraw.hipower.ltd'
client = mqtt.Client('mqtt_M101')
client.username_pw_set(username='hipowermqtt',password='hihi1234')
client.tls_set(ca_certs="/etc/ssl/certs/ca-certificates.crt")
client.on_connect=on_connect
client.on_message=on_message
print('Connecting to broker',broker)
client.connect(broker,8883)
client.loop_start()
inTI = time.time()
# Temp = Cursor.fetchone()
# RM = Temp[1]
# print(RM)
# SysRunTime = Temp[2]
# print(SysRunTime)

while (internet_on):
    inTI = time.time()
    if ( inTI - LastTi >= 10):
        inTI = time.time()
        try:
            #ser.write(Arduino)
            #buf = ser.read(32)
            #print(buf)
            #for i in range(len(buf)):
            #    break
            #Arduino = buf[4] + (buf[3] << 8)
            #print(Arduino)
            
            ser.write(Loadmeter_Vol)
            buf = ser.read(10)
            #print(buf)
            for i in range(len(buf)):
                break
            OutPutVol = buf[4] + (buf[3] << 8)
            #print(OutPutVol)
            ser.write(Loadmeter_Cur)
            buf = ser.read(10)
            #print(buf)
            for i in range(len(buf)):
                break
            OutPutCur = (buf[4] + (buf[3] << 8))
            if (OutPutCur > 10000):
                OutPutCur = (OutPutCur-65536)
            OutPutCur = OutPutCur
            #print(OutPutCur)
            ser.write(Loadmeter_Wat)
            buf = ser.read(10)
            for i in range(len(buf)):
                break
            OutPutWat = buf[6] + (buf[5] << 8)
            if (OutPutWat > 24000):
                OutPutWat = OutPutWat-65536
            #print(OutPutWat)
        except:
            print('Meter Error')
        try:
            ser.write(Temperature)
            time.sleep(0.3)
            buf = ser.read(15)
            #print(buf)
            for i in range(len(buf)):
                break
            T1 = int(buf[4] + (buf[3] << 8))
            if (T1 > 50000):
                T1 = 250
            #print(T1)
            T2 = int(buf[6] + (buf[5] << 8))
            if (T2 > 50000):
                T2 = 250
            #print(T2)
            T3 = int(buf[8] + (buf[7] << 8))
            if (T3 > 50000):
                T3 = 250
            #print(T3)
            T4 = int(buf[10] + (buf[9] << 8))
            if (T4 > 50000):
                T4 = 250
            #print(T4)
        except:
            T1 = 0
            T2 = 0
            T3 = 0
            T4 = 0
            #print('Temperature error')
        try:
            ser.write(PV)
            time.sleep(0.3)
            buf = ser.read(17)
            #print(buf)
            for i in range(len(buf)):
                break
            PV1V = int(buf[4] + (buf[3] << 8))
            #print(PV1V)
            PV1A = float(buf[6] + (buf[5] << 8))*0.1
            #print(PV1A)
            PV2V = int(buf[8] + (buf[7] << 8))
            #print(PV2V)
            PV2A = float(buf[10] + (buf[9] << 8))*0.1
            #print(PV2A)
            PVT = int(buf[12] + (buf[11] << 8))
            #print(PVT)
        except:
            PV1V = 0
            PV1A = 0
            PV2V = 0
            PV2A = 0
            PVT = 0
            print('PV error')
            
        if (inTI - SocTI >= 1):
            ser.write(Batmeter_Cur)
            buf = ser.read(10)
            #print(buf)
            for i in range(len(buf)):
                break
            BatCur = int(buf[4] + (buf[3] << 8))
            if (BatCur > 50000):
                BatCurSoc = BatCur-65536 
            else:
                BatCurSoc = BatCur
            #print(BatCurSoc)
            if (OutPutVol >= 3297):
                if (BatCurSoc < 10):
                    RM = 5994000
            #print(int(SOC))
            RM = int(RM + BatCurSoc)
            SOC = (RM/BatFCC) * 100
            SocTI = time.time()
            if (SOC >= 99.9):
                SOC = 99.9
                RM = 5994000
        BAT1 = round((float(OutPutVol/12)*0.1+0.54),2)
        BAT2 = round((float(OutPutVol/12)*0.1+0.32),2)
        BAT3 = round((float(OutPutVol/12)*0.1+0.23),2)
        BAT4 = round((float(OutPutVol/12)*0.1+0.45),2)
        BAT5 = round((float(OutPutVol/12)*0.1-0.54),2)
        BAT6 = round((float(OutPutVol/12)*0.1-0.32),2)
        BAT7 = round((float(OutPutVol/12)*0.1-0.23),2)
        BAT8 = round((float(OutPutVol/12)*0.1-0.45),2)
        BAT9 = round((float(OutPutVol/12)*0.1+0.32),2)
        BAT10 = round((float(OutPutVol/12)*0.1-0.32),2)
        BAT11 = round((float(OutPutVol/12)*0.1+0.11),2)
        BAT12 = round((float(OutPutVol/12)*0.1-0.11),2)
    
    #------------------H35K Server-------------------------------------------------------    
    from h35kModule import h35kModule_client, h35kModule_server
    import tangramModbus
    #------Module Setting--------------------

    h35k_001 = h35kModule_client(id='1680', ip='192.168.10.201', mac_addr='70:b3:d5:7b:84:cb')
    h35k_002 = h35kModule_client(id='1137', ip='192.168.10.200', mac_addr='70:b3:d5:7b:84:cb')
    h35k_003 = h35kModule_client(id='1681', ip='192.168.10.202', mac_addr='70:b3:d5:7b:84:cb')
    h35k_server = h35kModule_server([h35k_001, h35k_002, h35k_003])
    #-----------------------------------------
    # Create and start the thread to read Modbus messages
    # tangramModbus_thread = threading.Thread(target=tangramModbus.handle_modbus_message, args=())
    # tangramModbus_thread.start()

    h35k_server.start_client_threads()
    
    #----------------------------------------------------------------------------------------
    ModuleState = str(module1_State) +str(0) + str(0)
    ModuleTotalOutPut = module1_OutPutPower + module2_OutPutPower + module3_OutPutPower
    #print(ModuleTotalOutPut)
    TotalkW = module1_TotalWattHour + module2_TotalWattHour + module3_TotalWattHour
    #print(fuelLevel.voltage)
    FuelLevel = ((fuelLevel.voltage-3.44)/(1.48-3.44))*100#  0.83
    #if (FuelLevel <= 30):
    #    print('Low Fuel')
        #GPIO.output(PowerRelayControl, GPIO.HIGH)
    #elif(FuelLevel >= 100):
        #   print('High Fuel')
        #GPIO.output(PowerRelayControl, GPIO.LOW)
    if (FuelLevel <= 0):
        FuelLevel = 0
    elif (FuelLevel >= 100):
        FuelLevel = 100
    SystemHealth = (((OutPutVol - 2950)/(3250-2950)) * 90) + (FuelLevel * 0.1)
    if (SystemHealth <= 0):
        SystemHealth = 0
    elif (SystemHealth >= 100):
            SystemHealth = 100
    #print(SystemHealth)
    Overflow = '0'#GPIO.input(OverFolwDry)
    #if (Overflow == 0):
    #        Overflow = 1
    #elif(Overflow == 1):
    #        Overflow = 0
    leaksensor1 = '0'#GPIO.input(Leak)
    #if (leaksensor1 == 0):
    #        leaksensor1 = 1
    #elif(leaksensor1 == 1):
    #        leaksensor1 = 0
    leaksensor2 = '0'
    leaksensor = '%s%s'%(leaksensor1,leaksensor2)
    SystemAlert ='%s%s%s%s'%('0','0','0',Overflow)
    if (module1_State == 3 or module1_State == 4 or module1_State == 5 or module1_State == 6 or module1_State == 2 or module1_State == 9 or 
        module2_State == 3 or module2_State == 4 or module2_State == 5 or module2_State == 6 or module2_State == 2 or module2_State == 9 or 
        module3_State == 3 or module3_State == 4 or module3_State == 5 or module3_State == 6 or module3_State == 2 or module3_State == 9 ):
        GPIO.output(FuelPumControl, GPIO.HIGH)
        SysRunTimeStart = time.time()
        if (SysRunTimeStart - SysRunTimeStop >= 3600):
            SysRunTime = SysRunTime + 1
            SysRunTimeStop = time.time()
    # else:
    #     GPIO.output(FuelPumControl, GPIO.LOW)
    fuelConsume = ((module1_effic * module1_OutPutPower) * 0.9) + ((module3_effic * module3_OutPutPower) * 0.9) + ((module2_effic * module2_OutPutPower) * 0.9)
    fuelConsume = fuelConsume * 0.1
    #print(fuelConsume)
        #if (module1_State == 8 or module2_State == 8 or leaksensor1 >= 1 or OutPutVol <= 2950 or T1 > 700 or T2 > 500 or FuelLevel <=0):# or module3_State == 8):
            #if (inTI - SendGmailTi >= 7200):
                #ModuleErrorSendGmail()
                #SendGmailTi = time.time()
    
    if (sysAuto == 1):
        print("Hello")
        if (inTI - SetCMDTi >= 1):
            if (abs(ModuleTotalOutPut - sysOutPut) <= 50):
                module1_CurSet = module1_CurSet
                module2_CurSet = module2_CurSet
                module3_CurSet = module3_CurSet
            elif (ModuleTotalOutPut <= sysOutPut):
                module1_CurSet = module1_CurSet + 1
                module2_CurSet = module2_CurSet + 1
                module3_CurSet = module3_CurSet + 1
                SetCMDTi = time.time()
            elif(ModuleTotalOutPut <= sysOutPut):
                module1_CurSet = module1_CurSet - 1
                module2_CurSet = module2_CurSet - 1
                module3_CurSet = module3_CurSet - 1
                SetCMDTi = time.time()
    #OutPutWat1 = 11000
    if (inTI - SPECTI >= 9):
        if (OutPutWat > 6000):
            try:
                print("I am here! OutPutWat > 6000")
                dataupload = {
                    'inTI':int(inTI),
                    'A0100':SystemID,
                    'A0101':int(SystemHealth),
                    'A0201':OutPutWat,
                    'A0300':ModuleState,
                    'A0700':OutPutVol,
                    'A0800':T1,
                    'A0801':T2,
                    'A0802':T3,
                    'A0803':T4,
                    'A0900':TotalkW,
                    'FC1V':module1_StackVol,
                    'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    'FC2V':module2_StackVol,
                    'FC2A':module2_StackCur,
                    'FC2T':module2_StackTemp,
                    'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                    'A0200':sysOutPut,
                    'FC1TI':module1_TotalOperHour,
                    'FC2AC':module2_TotalWattHour,
                    'FC2TI':module2_TotalOperHour,
                    'PV1V':PV1V,
                    'PV1A':PV1A,
                    'PV2V':PV2V,
                    'PV2A':PV2A,
                    'PVT':PVT,
                    'PVC':2,
                    'FC3TI':module3_TotalOperHour,
                    'FC3OA':module3_OutPutCur,
                    'FC3OW':module3_OutPutPower,
                    'FC3SC':module3_TotalCycleHour,
                    'FC3V':module3_StackVol,
                    'FC3AC':module3_TotalWattHour,
                    'FC3A':module3_StackCur,
                    'FC3T':module3_StackTemp,
                    'FC3P':module3_StackCoolantPre,
                    'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
                    'FCTW':ModuleTotalOutPut,
                    'A1000':int(FuelLevel),
                    'BATC':0,
                    'A0600':SystemAlert,
                    'A0400':str(0),
                    'A0500':leaksensor,
                    'BATCC':BatCur,
                    'SOC':SOC,
                    'A0804':250,
                    'A0805':250,
                    'A0806':250,
                    'A0807':250,
                    'FC1H':module1,
                    'FC2H':module2,
                    'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                    'lastTI':int(dataLasTI),
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                    'FC3H':module3,
                    'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)
                    }
                upload = requests.post(url,json = dataupload)
                UpdateDate = 0
                SPECTI = time.time()
                print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
                #print(int(SOC))
                #print(dataupload)
                #print(OutPutVol)
            except:
                print('OutPutWat Upload ERROR')
        if (OutPutVol > 3350 or OutPutVol < 2950):
            print("I am here! OutPutVol > 3350 or OutPutVol < 2950")
            try:
                dataupload = {
                    'inTI':int(inTI),
                    'A0100':SystemID,
                    'A0101':int(SystemHealth),
                    'A0201':OutPutWat,
                    'A0300':ModuleState,
                    'A0700':OutPutVol,
                    'A0800':T1,
                    'A0801':T2,
                    'A0802':T3,
                    'A0803':T4,
                    'A0900':TotalkW,
                    'FC1V':module1_StackVol,
                    'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    'FC2V':module2_StackVol,
                    'FC2A':module2_StackCur,
                    'FC2T':module2_StackTemp,
                    'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                    'A0200':sysOutPut,
                    'FC1TI':module1_TotalOperHour,
                    'FC2AC':module2_TotalWattHour,
                    'FC2TI':module2_TotalOperHour,
                    'PV1V':PV1V,
                    'PV1A':PV1A,
                    'PV2V':PV2V,
                    'PV2A':PV2A,
                    'PVT':PVT,
                    'PVC':2,
                    'FC3TI':module3_TotalOperHour,
                    'FC3OA':module3_OutPutCur,
                    'FC3OW':module3_OutPutPower,
                    'FC3SC':module3_TotalCycleHour,
                    'FC3V':module3_StackVol,
                    'FC3AC':module3_TotalWattHour,
                    'FC3A':module3_StackCur,
                    'FC3T':module3_StackTemp,
                    'FC3P':module3_StackCoolantPre,
                    'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
                    'FCTW':ModuleTotalOutPut,
                    'A1000':int(FuelLevel),
                    'BATC':0,
                    'A0600':SystemAlert,
                    'A0400':str(0),
                    'A0500':leaksensor,
                    'BATCC':BatCur,
                    'SOC':SOC,
                    'A0804':250,
                    'A0805':250,
                    'A0806':250,
                    'A0807':250,
                    'FC1H':module1,
                    'FC2H':module2,
                    'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                    'lastTI':int(dataLasTI),
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                    'FC3H':module3,
                    'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)
                    }
                upload = requests.post(url,json = dataupload)
                UpdateDate = 0
                SPECTI = time.time()
                print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
                #print(int(SOC))
                #print(dataupload)
                #print(OutPutVol)
            except:
                print('OutPutVol Upload ERROR')
        if (T4 > 700):
            print("I am here! T4 > 700")
            try:
                dataupload = {
                    'inTI':int(inTI),
                    'A0100':SystemID,
                    'A0101':int(SystemHealth),
                    'A0201':OutPutWat,
                    'A0300':ModuleState,
                    'A0700':OutPutVol,
                    'A0800':T1,
                    'A0801':T2,
                    'A0802':T3,
                    'A0803':T4,
                    'A0900':TotalkW,
                    'FC1V':module1_StackVol,
                    'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    'FC2V':module2_StackVol,
                    'FC2A':module2_StackCur,
                    'FC2T':module2_StackTemp,
                    'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                    'A0200':sysOutPut,
                    'FC1TI':module1_TotalOperHour,
                    'FC2AC':module2_TotalWattHour,
                    'FC2TI':module2_TotalOperHour,
                    'PV1V':PV1V,
                    'PV1A':PV1A,
                    'PV2V':PV2V,
                    'PV2A':PV2A,
                    'PVT':PVT,
                    'PVC':2,
                    'FC3TI':module3_TotalOperHour,
                    'FC3OA':module3_OutPutCur,
                    'FC3OW':module3_OutPutPower,
                    'FC3SC':module3_TotalCycleHour,
                    'FC3V':module3_StackVol,
                    'FC3AC':module3_TotalWattHour,
                    'FC3A':module3_StackCur,
                    'FC3T':module3_StackTemp,
                    'FC3P':module3_StackCoolantPre,
                    'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
                    'FCTW':ModuleTotalOutPut,
                    'A1000':int(FuelLevel),
                    'BATC':0,
                    'A0600':SystemAlert,
                    'A0400':str(0),
                    'A0500':leaksensor,
                    'BATCC':BatCur,
                    'SOC':SOC,
                    'A0804':250,
                    'A0805':250,
                    'A0806':250,
                    'A0807':250,
                    'FC1H':module1,
                    'FC2H':module2,
                    'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                    'lastTI':int(dataLasTI),
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                    'FC3H':module3,
                    'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)
                    }
                upload = requests.post(url,json = dataupload)
                UpdateDate = 0
                SPECTI = time.time()
                print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
                #print(int(SOC))
                #print(dataupload)
                #print(OutPutVol)
            except:
                print('Temperature Upload ERROR')
        if (FuelLevel < 20 or FuelLevel > 100):
            print("I am here! FuelLevel < 20 or FuelLevel > 100")
            try:
                dataupload = {
                    'inTI':int(inTI),
                    'A0100':SystemID,
                    'A0101':int(SystemHealth),
                    'A0201':OutPutWat,
                    'A0300':ModuleState,
                    'A0700':OutPutVol,
                    'A0800':T1,
                    'A0801':T2,
                    'A0802':T3,
                    'A0803':T4,
                    'A0900':TotalkW,
                    'FC1V':module1_StackVol,
                    'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    'FC2V':module2_StackVol,
                    'FC2A':module2_StackCur,
                    'FC2T':module2_StackTemp,
                    'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                    'A0200':sysOutPut,
                    'FC1TI':module1_TotalOperHour,
                    'FC2AC':module2_TotalWattHour,
                    'FC2TI':module2_TotalOperHour,
                    'PV1V':PV1V,
                    'PV1A':PV1A,
                    'PV2V':PV2V,
                    'PV2A':PV2A,
                    'PVT':PVT,
                    'PVC':2,
                    'FC3TI':module3_TotalOperHour,
                    'FC3OA':module3_OutPutCur,
                    'FC3OW':module3_OutPutPower,
                    'FC3SC':module3_TotalCycleHour,
                    'FC3V':module3_StackVol,
                    'FC3AC':module3_TotalWattHour,
                    'FC3A':module3_StackCur,
                    'FC3T':module3_StackTemp,
                    'FC3P':module3_StackCoolantPre,
                    'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
                    'FCTW':ModuleTotalOutPut,
                    'A1000':int(FuelLevel),
                    'BATC':0,
                    'A0600':SystemAlert,
                    'A0400':str(0),
                    'A0500':leaksensor,
                    'BATCC':BatCur,
                    'SOC':SOC,
                    'A0804':250,
                    'A0805':250,
                    'A0806':250,
                    'A0807':250,
                    'FC1H':module1,
                    'FC2H':module2,
                    'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                    'lastTI':int(dataLasTI),
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                    'FC3H':module3,
                    'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)
                    }
                upload = requests.post(url,json = dataupload)
                UpdateDate = 0
                SPECTI = time.time()
                print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
                #print(int(SOC))
                #print(dataupload)
                #print(OutPutVol)
            except:
                print('FuelLevel Upload ERROR')
        if (Overflow == 1):
            print("I am here! Overflow == 1")
            try:
                dataupload = {
                    'inTI':int(inTI),
                    'A0100':SystemID,
                    'A0101':int(SystemHealth),
                    'A0201':OutPutWat,
                    'A0300':ModuleState,
                    'A0700':OutPutVol,
                    'A0800':T1,
                    'A0801':T2,
                    'A0802':T3,
                    'A0803':T4,
                    'A0900':TotalkW,
                    'FC1V':module1_StackVol,
                    'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    'FC2V':module2_StackVol,
                    'FC2A':module2_StackCur,
                    'FC2T':module2_StackTemp,
                    'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                    'A0200':sysOutPut,
                    'FC1TI':module1_TotalOperHour,
                    'FC2AC':module2_TotalWattHour,
                    'FC2TI':module2_TotalOperHour,
                    'PV1V':PV1V,
                    'PV1A':PV1A,
                    'PV2V':PV2V,
                    'PV2A':PV2A,
                    'PVT':PVT,
                    'PVC':2,
                    'FC3TI':module3_TotalOperHour,
                    'FC3OA':module3_OutPutCur,
                    'FC3OW':module3_OutPutPower,
                    'FC3SC':module3_TotalCycleHour,
                    'FC3V':module3_StackVol,
                    'FC3AC':module3_TotalWattHour,
                    'FC3A':module3_StackCur,
                    'FC3T':module3_StackTemp,
                    'FC3P':module3_StackCoolantPre,
                    'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
                    'FCTW':ModuleTotalOutPut,
                    'A1000':int(FuelLevel),
                    'BATC':0,
                    'A0600':SystemAlert,
                    'A0400':str(0),
                    'A0500':leaksensor,
                    'BATCC':BatCur,
                    'SOC':SOC,
                    'A0804':250,
                    'A0805':250,
                    'A0806':250,
                    'A0807':250,
                    'FC1H':module1,
                    'FC2H':module2,
                    'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                    'lastTI':int(dataLasTI),
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                    'FC3H':module3,
                    'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)
                    }
                upload = requests.post(url,json = dataupload)
                UpdateDate = 0
                SPECTI = time.time()
                print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
                #print(int(SOC))
                #print(dataupload)
                #print(OutPutVol)
            except:
                print('Overflow Upload ERROR')
    if(UpdateDate == 1):
        print("I am here! UpdateDate == 1")
        try:
            ModuleState = str(module1_State) + str(0) + str(0)
            print(ModuleState)
            dataupload = {
                    'inTI':int(inTI),
                    'A0100':SystemID,
                    'A0101':int(SystemHealth),
                    'A0201':OutPutWat,
                    'A0300':ModuleState,
                    'A0700':OutPutVol,
                    'A0800':T1,
                    'A0801':T2,
                    'A0802':T3,
                    'A0803':T4,
                    'A0900':TotalkW,
                    'FC1V':module1_StackVol,
                    'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    'FC2V':module2_StackVol,
                    'FC2A':module2_StackCur,
                    'FC2T':module2_StackTemp,
                    'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                    'A0200':sysOutPut,
                    'FC1TI':module1_TotalOperHour,
                    'FC2AC':module2_TotalWattHour,
                    'FC2TI':module2_TotalOperHour,
                    'PV1V':PV1V,
                    'PV1A':PV1A,
                    'PV2V':PV2V,
                    'PV2A':PV2A,
                    'PVT':PVT,
                    'PVC':2,
                    'FC3TI':module3_TotalOperHour,
                    'FC3OA':module3_OutPutCur,
                    'FC3OW':module3_OutPutPower,
                    'FC3SC':module3_TotalCycleHour,
                    'FC3V':module3_StackVol,
                    'FC3AC':module3_TotalWattHour,
                    'FC3A':module3_StackCur,
                    'FC3T':module3_StackTemp,
                    'FC3P':module3_StackCoolantPre,
                    'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
                    'FCTW':ModuleTotalOutPut,
                    'A1000':int(FuelLevel),
                    'BATC':0,
                    'A0600':SystemAlert,
                    'A0400':str(0),
                    'A0500':leaksensor,
                    'BATCC':BatCur,
                    'SOC':SOC,
                    'A0804':250,
                    'A0805':250,
                    'A0806':250,
                    'A0807':250,
                    'FC1H':module1,
                    'FC2H':module2,
                    'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                    'lastTI':int(dataLasTI),
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                    'FC3H':module3,
                    'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)
                    }
            upload = requests.post(url,json = dataupload)
            UpdateDate = 0
            print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
            #print(leaksensor)
            #print(int(SOC))
            #print(dataupload)
            #print(OutPutVol)
        except:
            print('Non-Routine Data Upload ERROR')
    if (inTI - dataLasTI >= 59):
        print("I am here! inTI - dataLasTI >= 59")
        try:
            dataLasTI = time.time()
            # print(dataLasTI)
            dataupload = {
                'inTI':int(dataLasTI),
                'A0100':SystemID,
                'A0101':int(SystemHealth),
                'A0201':OutPutWat,
                'A0300':ModuleState,
                'A0700':OutPutVol,
                'A0800':T1,
                'A0801':T2,
                'A0802':T3,
                'A0803':T4,
                'A0900':TotalkW,
                'FC1V':module1_StackVol,
                'A1001':fuelConsume,
                'FC1A':module1_StackCur,
                'FC1T':module1_StackTemp,
                'FC1P':module1_StackCoolantPre,
                'FC2V':module2_StackVol,
                'FC2A':module2_StackCur,
                'FC2T':module2_StackTemp,
                'FC2P':module2_StackCoolantPre,
                'FC1AC':module1_TotalWattHour,
                'FC1OA':module1_OutPutCur,
                'FC1TI':module1_TotalOperHour,
                'FC2AC':module2_TotalWattHour,
                'FC2TI':module2_TotalOperHour,
                'PV1V':PV1V,
                'PV1A':PV1A,
                'PV2V':PV2V,
                'PV2A':PV2A,
                'PVT':PVT,
                'PVC':2,
                'FC3TI':module3_TotalOperHour,
                'FC3OA':module3_OutPutCur,
                'FC3OW':module3_OutPutPower,
                'FC3SC':module3_TotalCycleHour,
                'FC3V':module3_StackVol,
                'FC3AC':module3_TotalWattHour,
                'FC3A':module3_StackCur,
                'FC3T':module3_StackTemp,
                'FC3P':module3_StackCoolantPre,
                'FC3H':module3,
                'FC2OA':module2_OutPutCur,
                'FC1OW':module1_OutPutPower,
                'FC2OW':module2_OutPutPower,
                'FC1SC':module1_TotalCycleHour,
                'FC2SC':module2_TotalCycleHour,
                'FCC':3,
                'TA':OutPutCur,
                'FCTW':ModuleTotalOutPut,
                'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                'A0200':sysOutPut,
                'A1000':int(FuelLevel),
                'BATC':0,
                'A0600':SystemAlert,
                'A0400':str(0),
                'A0500':leaksensor,
                'BATCC':BatCur,
                'SOC':SOC,
                'A0804':250,
                'A0805':250,
                'A0806':250,
                'A0807':250,
                'FC1H':module1,
                'FC2H':module2,
                'sysRT':SysRunTime,
                'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet),
                'BATC':12,
                'BAT1V':BAT1,
                'BAT2V':BAT2,
                'BAT3V':BAT3,
                'BAT4V':BAT4,
                'BAT5V':BAT5,
                'BAT6V':BAT6,
                'BAT7V':BAT7,
                'BAT8V':BAT8,
                'BAT9V':BAT9,
                'BAT10V':BAT10,
                'BAT11V':BAT11,
                'BAT12V':BAT12}
            
            print(dataupload)
            upload = requests.post(url,json = dataupload)
            print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))

            # tangramData contains 30 registers. Now with 26 valid data. And 4 placeholders as 0.
            tangramData = [
                OutPutWat, TotalkW/10, OutPutVol/10, OutPutCur/100, T4/10,
                FuelLevel, leaksensor1+Overflow,
                module1, module1_State, module1_TotalCycleHour/10, module1_OutPutCur/10, module1_effic,
                module2, module2_State, module2_TotalCycleHour/10, module2_OutPutCur/10, module2_effic,
                module3, module3_State, module3_TotalCycleHour/10, module3_OutPutCur/10, module3_effic,
                PV2A/10, PVT/10,
                SOC, BatCurSoc/100,
                0,0,0,0
                ]
            print(tangramData)                
            modbus_packet = tangramModbus.create_modbus_packet(1, 16, tangramData)
            print(modbus_packet)

            # Open serial port and send the packet, then close the ser
            # with serial.Serial('/dev/ttyUSB1', 9600, timeout=1) as ser:
            #     ser.write(modbus_packet)

        except:
            print('Data Upload ERROR')


    # if (OutPutVol < 3000): #Situation 1: Without charging load. Consume power normally.int(SOC) < 4 and OutPutWat <= 7000
    #     print("Situiation 1: Without charging load. Consume power normally")
    #     SetCMD = 1
    #     if (SetCMD == 1):
    #         if (module1_State == 1):
    #             Module1_Request_start = '01'
    #             if (module1_State == 8 or module1_State == 7 or module1_State == 6):
    #                 pass
    #                 # Module3_Request_start = '01' #原本是Module2 (2022-08-05 Robert)
    #                 #if (module2_State == 8 or module2_State == 7 or module2_State == 6):
    #                    # Module3_Request_start = '01'
    #                 # if (module3_State != 1):
    #                 #     Module3_Request_start = '00' 
    #         else:
    #             Module1_Request_start = '00'
                
    """elif (int(SOC) < 4 and  7000 < OutPutWat <= 9000): #Situation2: With one charging load.
        print("Situiation 2: With one charging load")
        SetCMD = 2
        if (SetCMD == 2):
            if (module1_State == 1):
                Module1_Request_start = '01'
                if (module1_State == 8 or module1_State == 7 or module1_State == 6):
                    Module3_Request_start = '01' #原本是Module2 (2022-08-05 Robert)
                    #if (module2_State == 8 or module2_State == 7 or module2_State == 6):
                        # Module3_Request_start = '01'
                    if (module3_State != 1):
                        Module3_Request_start = '00' 
            else:
                Module1_Request_start = '00'
                
    elif (int(SOC) < 4 and 9000 < OutPutWat): #Situation3: With two or three charging load.
        print("Situiation 3: With two or three charging load")
        SetCMD = 3
        if (module1_State == 1):
            Module1_Request_start = '00'
            # if (module2_State == 1):
                # Module2_Request_start = '00'
            if (module3_State == 1):
                Module3_Request_start = '00'"""
            
            

    LastTI = time.time()
    #print(OutPutVol)
    #print(OutPutWat)
    #print(PV1A)
    #print(module1_State)
    #print(module2_State)
    #print(module3_State)         
    #print(LastTI - inTI)

# Wait for the Modbus thread to exit
# tangramModbus.stop_modbus_thread = True
# tangramModbus_thread.join()

