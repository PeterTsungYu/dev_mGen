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
module1_CurSet = 180
module2_CurSet = 180
module3_CurSet = 180
CurSet_HIGH = 40
CurSet_HIGHEST = 850
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
FuelPumControl = 17
PowerRelayControl = 27
BatDry = 22
Leak = 23
TACH = 24       # Fan's tachometer output pin
OverFolwDry = 25
PULSE = 2       # Noctua fans puts out two pluses per revolution
FAN_PIN = 18            # PWM 控制腳位，設定成你想接的位置即可，注意是 BCM 編號
PV1V = 0
PV1A = 0
PV2V = 0
PV2A = 0
PVT = 0
#--------------------------------------------------------------
TCPport = 44818
UDPport = 2222
UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP.bind(('0.0.0.0',UDPport))
UDP.settimeout(0.5)
#UDP.setblocking(0)
#-----------------http Config----------------------------------
#host = 'http://api.thingspeak.com'
#readAPIkey = '6XSVMSZFELCGMYSB'
#writeAPIkey = 'AOJX2AZP50W1NWKH'
#channelId = '1271239'
#url_SysRuntime = '%s/channels/%s/feeds/last.json?api_key=%s'%(host,channelId,readAPIkey)
url = 'http://upraw.hipower.ltd:9999/recv?v=1'
#--------------------------------------------------------------
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
#----------------------------------------------------------------
#-----------------GPIO Setting---------------------------------
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
#-----------------SMTP Config Gmail Sending--------------------
GUser = 'phil@hipower.ltd'
GPass = 'qwe751212'
GFrom = GUser
to_address = ['pokhts@gmail.com''mick@hipower.pro','scott@hipower.pro','robert@hipower.pro','scott.chen@m-field.com.tw',
              'x19861012@gmail.com','sunnydengjyun@gmail.com']
Subject = 'Warnning!! System M101'
#--------------------------------------------------------------
#-----------------SQLite Setting-------------------------------
DBsave = sqlite3.connect("M101.db")
Cursor = DBsave.cursor()
Sysdata_list = []
#------------------------------------------------------------------
#-----------------SerialPort Config---------------------------
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
#------Module Setting--------------------
module1_IP = '192.168.10.200'
Module1_currentset = struct.pack('f',18)
module2_IP = '192.168.10.201'
Module2_currentset = struct.pack('f',18)
module3_IP = '192.168.10.202'
Module3_currentset = struct.pack('f',18)
Module1_Request_start ='00'
Module1_Request_stop ='00'
Module1_Request_reset = '00'
Module2_Request_start ='00'
Module2_Request_stop ='00'
Module2_Request_reset = '00'
Module3_Request_start ='00'
Module3_Request_stop ='00'
Module3_Request_reset = '00'
#-----------------------------------------

def get_module1_data(module1_IP): #Module1 EthernertIP 抓資料
    global Module1_currentset,Module1_Enable,Module1_Request_start,Module1_Request_stop,Module1_Request_reset,module1
    Module1_Register =  bytes.fromhex('65000400000000000000000000000000000000000000000001000000')
    Module1_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Module1_TCP.connect((module1_IP, TCPport))
    Module1_TCP.sendall(Module1_Register)
    Module1_TCPmessage = Module1_TCP.recv(1024)
    Module1_Session = Module1_TCPmessage[4:8].hex()
    Module1_Identity = bytes.fromhex('%s%s%s'%('6f001600',Module1_Session,'00000000000000000000000000000000000000000000020000000000b2000600010220012401'))
    Module1_TCP.sendall(Module1_Identity)
    Module1_TCPmessage = Module1_TCP.recv(1024)
    module1ID_1 = Module1_TCPmessage[54:55].hex()
    module1ID_2 = Module1_TCPmessage[55:56].hex()
    module1 = int((module1ID_2 + module1ID_1),base=16)
    Module1_ForwardOpen = bytes.fromhex('%s%s%s'%('6f004000',Module1_Session,'00000000000000000000000000000000000000000000020000000000b20030005402200624010a0a0200550e0300550e550edafa0df0ad8b00000000c0c300002e46c0c300007a40010320042c702c64'))
    Module1_ForwardClose = bytes.fromhex('%s%s%s'%('6f002800',Module1_Session,'00000000000000000000000000000000000000000000020000000000b20018004e02200624010a0a550edafa0df0ad8b030020042c702c64'))
    Module1_Enable = '01'
    Module1_Seq = '00000000'
    Module1_CIPSeq = '0000'
    Module1_currentset = struct.pack('f',(module1_CurSet)*0.1)
    Module1_CurSet = ''.join(['%02x' % b for b in Module1_currentset])
    Module1_CMD = '%s%s%s%s%s%s' %(Module1_Enable,Module1_Request_start,Module1_Request_stop,Module1_Request_reset,Module1_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    if(int(SOC) < 80):
        Module1_currentset = struct.pack('f',(CurSet_HIGH)*0.1) #Module1 current set 51A
        Module1_CurSet = ''.join(['%02x' % b for b in Module1_currentset])
        Module1_CMD = '%s%s%s%s%s%s' %(Module1_Enable,Module1_Request_start,Module1_Request_stop,Module1_Request_reset,Module1_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    if(9000 < OutPutWat):
        Module1_currentset = struct.pack('f',(CurSet_HIGHEST)*0.1)  #Module3 current set 85A
        Module1_CurSet = ''.join(['%02x' % b for b in Module1_currentset])
        Module1_CMD = '%s%s%s%s%s%s' %(Module1_Enable,Module1_Request_start,Module1_Request_stop,Module1_Request_reset,Module1_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    Module1_TCP.sendall(Module1_ForwardOpen)
    Module1_TCPmessage = Module1_TCP.recv(1024)
    #print(Module1_Hexmessage)
    Module1_O2TID = Module1_TCPmessage[44:48].hex()
    Module1_T2OID = Module1_TCPmessage[48:52].hex()
    #time.sleep(0.1)
    k = 0
    while k <= 1:
        try:
            Module1_O2T = bytes.fromhex('%s%s%s%s%s%s%s'%('020002800800',Module1_O2TID,Module1_Seq,'b1002e00',Module1_CIPSeq,'01000000',Module1_CMD))
            UDP.sendto(Module1_O2T,(module1_IP,UDPport))
            try:
                Module1_T2O,M1addr = UDP.recvfrom(150)
                Module1_Seq = Module1_T2O[10:14].hex()
                Module1_CIPSeq = Module1_T2O[18:20].hex()
                k = k +1
            except socket.timeout as e:
                print('Module1 UDP Timeout')
                k = 5
        except:
            print('Module1_O2T error')
    Module1_TCP.sendall(Module1_ForwardClose)
    Module1_TCPmessage = Module1_TCP.recv(1024)
    Module1_Request_reset = '00'
    Module1_TCP.close()
    if (M1addr[0] == module1_IP):
        return Module1_T2O


def get_module2_data(module2_IP):
    global Module2_currentset,Module2_Enable,Module2_Request_start,Module2_Request_stop,Module2_Request_reset,module2
    Module2_Register =  bytes.fromhex('65000400000000000000000000000000000000000000000001000000')
    Module2_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Module2_TCP.connect((module2_IP, TCPport))
    Module2_TCP.sendall(Module2_Register)
    Module2_TCPmessage = Module2_TCP.recv(1024)
    Module2_Session = Module2_TCPmessage[4:8].hex()
    Module2_Identity = bytes.fromhex('%s%s%s'%('6f001600',Module2_Session,'00000000000000000000000000000000000000000000020000000000b2000600010220012401'))
    Module2_TCP.sendall(Module2_Identity)
    Module2_TCPmessage = Module2_TCP.recv(1024)
    module2ID_1 = Module2_TCPmessage[54:55].hex()
    module2ID_2 = Module2_TCPmessage[55:56].hex()
    module2 = int((module2ID_2 + module2ID_1),base=16)
    Module2_ForwardOpen = bytes.fromhex('%s%s%s'%('6f004000',Module2_Session,'00000000000000000000000000000000000000000000020000000000b20030005402200624010a0a02004c6103004c614c61dafa0df0ad8b00000000c0c300002e46c0c300007a40010320042c702c64'))
    Module2_ForwardClose = bytes.fromhex('%s%s%s'%('6f002800',Module2_Session,'00000000000000000000000000000000000000000000020000000000b20018004e02200624010a0a4c61dafa0df0ad8b030020042c702c64'))
    Module2_Enable = '01'
    Module2_Seq = '00000000'
    Module2_CIPSeq = '0000'
    Module2_currentset = struct.pack('f',(module2_CurSet)*0.1)
    Module2_CurSet = ''.join(['%02x' % b for b in Module2_currentset])
    Module2_CMD = '%s%s%s%s%s%s' %(Module2_Enable,Module2_Request_start,Module2_Request_stop,Module2_Request_reset,Module2_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    if(int(SOC) < 80):
        Module2_currentset = struct.pack('f',(CurSet_HIGH)*0.1)  #Module2 current set 51A
        Module2_CurSet = ''.join(['%02x' % b for b in Module2_currentset])
        Module2_CMD = '%s%s%s%s%s%s' %(Module2_Enable,Module2_Request_start,Module2_Request_stop,Module2_Request_reset,Module2_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    if(9000 < OutPutWat):
        Module2_currentset = struct.pack('f',(CurSet_HIGHEST)*0.1)  #Module3 current set 85A
        Module2_CurSet = ''.join(['%02x' % b for b in Module2_currentset])
        Module2_CMD = '%s%s%s%s%s%s' %(Module2_Enable,Module2_Request_start,Module2_Request_stop,Module2_Request_reset,Module2_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    Module2_TCP.sendall(Module2_ForwardOpen)
    Module2_TCPmessage = Module2_TCP.recv(1024)
    Module2_O2TID = Module2_TCPmessage[44:48].hex()
    Module2_T2OID = Module2_TCPmessage[48:52].hex()
    #time.sleep(0.1)
    k = 0
    while k <= 1:
        try:
            Module2_O2T = bytes.fromhex('%s%s%s%s%s%s%s'%('020002800800',Module2_O2TID,Module2_Seq,'b1002e00',Module2_CIPSeq,'01000000',Module2_CMD))
            UDP.sendto(Module2_O2T,(module2_IP,UDPport))
            try:
                Module2_T2O,M2addr = UDP.recvfrom(150)
                Module2_Seq = Module2_T2O[10:14].hex()
                Module2_CIPSeq = Module2_T2O[18:20].hex()
                k = k +1
            except socket.timeout as e:
                print('Module2 UDP Timeout')
                k = 5
        except:
            print('Module2_O2T error')
    Module2_TCP.sendall(Module2_ForwardClose)
    Module2_TCPmessage = Module2_TCP.recv(1024)
    Module2_Request_reset = '00'
    Module2_TCP.close()
    if (M2addr[0] == module2_IP):
        return Module2_T2O


def get_module3_data(module3_IP):
    global Module3_currentset,Module3_Enable,Module3_Request_start,Module3_Request_stop,Module3_Request_reset,module3
    Module3_Register =  bytes.fromhex('65000400000000000000000000000000000000000000000001000000')
    Module3_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Module3_TCP.connect((module3_IP, TCPport))
    Module3_TCP.sendall(Module3_Register)
    Module3_TCPmessage = Module3_TCP.recv(1024)
    Module3_Session = Module3_TCPmessage[4:8].hex()
    Module3_Identity = bytes.fromhex('%s%s%s'%('6f001600',Module3_Session,'00000000000000000000000000000000000000000000020000000000b2000600010220012401'))
    Module3_TCP.sendall(Module3_Identity)
    Module3_TCPmessage = Module3_TCP.recv(1024)
    module3ID_1 = Module3_TCPmessage[54:55].hex()
    module3ID_2 = Module3_TCPmessage[55:56].hex()
    module3 = int((module3ID_2 + module3ID_1),base=16)
    Module3_ForwardOpen = bytes.fromhex('%s%s%s'%('6f004000',Module3_Session,'00000000000000000000000000000000000000000000020000000000b20030005402200624010a0a02004c6103004c614c61dafa0df0ad8b00000000c0c300002e46c0c300007a40010320042c702c64'))
    Module3_ForwardClose = bytes.fromhex('%s%s%s'%('6f002800',Module3_Session,'00000000000000000000000000000000000000000000020000000000b20018004e02200624010a0a4c61dafa0df0ad8b030020042c702c64'))
    Module3_Enable = '01'
    Module3_Seq = '00000000'
    Module3_CIPSeq = '0000'
    Module3_currentset = struct.pack('f',(module3_CurSet)*0.1)
    Module3_CurSet = ''.join(['%02x' % b for b in Module3_currentset])
    Module3_CMD = '%s%s%s%s%s%s' %(Module3_Enable,Module3_Request_start,Module3_Request_stop,Module3_Request_reset,Module3_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    if(int(SOC) < 80):
        Module3_currentset = struct.pack('f',(CurSet_HIGH)*0.1)  #Module3 current set 51A
        Module3_CurSet = ''.join(['%02x' % b for b in Module3_currentset])
        Module3_CMD = '%s%s%s%s%s%s' %(Module3_Enable,Module3_Request_start,Module3_Request_stop,Module3_Request_reset,Module3_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    if(9000 < OutPutWat):
        Module3_currentset = struct.pack('f',(CurSet_HIGHEST)*0.1)  #Module3 current set 85A
        Module3_CurSet = ''.join(['%02x' % b for b in Module3_currentset])
        Module3_CMD = '%s%s%s%s%s%s' %(Module3_Enable,Module3_Request_start,Module3_Request_stop,Module3_Request_reset,Module3_CurSet,'0000000000000000000000000000000000000000000000000000000000000000')
    Module3_TCP.sendall(Module3_ForwardOpen)
    Module3_TCPmessage = Module3_TCP.recv(1024)
    Module3_O2TID = Module3_TCPmessage[44:48].hex()
    Module3_T2OID = Module3_TCPmessage[48:52].hex()
    k = 0
    while k <= 2:
        try:
            Module3_O2T = bytes.fromhex('%s%s%s%s%s%s%s'%('020002800800',Module3_O2TID,Module3_Seq,'b1002e00',Module3_CIPSeq,'01000000',Module3_CMD))
            UDP.sendto(Module3_O2T,(module3_IP,UDPport))
            try:
                Module3_T2O,M3addr = UDP.recvfrom(150)
                Module3_Seq = Module3_T2O[10:14].hex()
                Module3_CIPSeq = Module3_T2O[18:20].hex()
                k = k +1
            except socket.timeout as e:
                print('Module3 UDP Timeout')
                k = 5
        except:
            print('Module1_O2T error')
    Module3_TCP.sendall(Module3_ForwardClose)
    Module3_TCPmessage = Module3_TCP.recv(1024)
    Module3_Request_reset = '00'
    Module3_TCP.close()
    if (M3addr[0] == module3_IP):
        return Module3_T2O


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
    rpm = (freq / PULSE) * 60
    t = time.time()
    
def ModuleErrorSendGmail(): #錯誤訊息發Mail
    if (module1_State == 7 or module1_State == 8):
        contents = '%s.%s'%('module1 error please check',module1)
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        print('module1_error')
        """
    elif (module2_State == 7 or module2_State == 8):
        contents = '%s.%s'%('module2 error please check',module2)
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        print('module2_error')
        """
    elif (module3_State == 7 or module3_State == 8):
        contents = '%s.%s'%('module3 error please check',module3)
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        
    elif (OutputVol <= 3050):
        contents = '%s.%s'%('System Voltage Low please check',OutputVol)
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        print('System Voltage Low')
    elif (T4 >= 700):
        contents = '%s.%s'%('System Temperature High please Check',T4)
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        print('System temperature High')
        """
    elif (T2 >= 500):
        contents = '%s.%s'%('Battery Temperature High please Check',T2)
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        """
    elif (leaksensor >= 2):
        contents = 'Fuel or TEG Leak please check'
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        print('Fuel or TEG Leak')
    elif (FuelLevel <= 0):
        contents = 'Fuel tank is empty please check'
        mail = MIMEMultipart()
        mail['From'] = GFrom
        mail['To'] = ','.join(to_address)
        mail['Subject'] = Subject
        mail.attach(MIMEText(contents))
        smtpserver = smtplib.SMTP_SSL("smtp.gmail.com",465)
        smtpserver.ehlo()
        smtpserver.login(GUser,GPass)
        smtpserver.sendmail(GFrom,to_address,mail.as_string())
        smtpserver.quit()
        print('Fuel empty')
        
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
        if(RemoteCmd == 'FC_Control_Current'):
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
            
        elif(RemoteCmd == 'FC_Control_Start'):
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
            
        elif(RemoteCmd == 'FC_Control_Stop'):
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
        elif(RemoteCmd == 'FC_Control_Reset'):
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
        elif(RemoteCmd == 'FC_Control_Enable'):
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
        elif(RemoteCmd == 'SYS_Control_Power'):
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
#Cursor.execute("create table Sysdata(TI,RM,Runtime)")
#Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,4620000,114))
#DBsave.commit()
Cursor.execute("SELECT * FROM Sysdata ORDER BY TI DESC LIMIT 1")
Temp = Cursor.fetchone()
RM = Temp[1]
print(RM)
SysRunTime = Temp[2]
print(SysRunTime)


while (internet_on):
    #try:
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
                print(module1_OutPutVol)
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
        #------------------Module1 data-------------------------------------------------------
        try:
            module1_data = get_module1_data(module1_IP)
            module1_Requested_state = int.from_bytes(module1_data[20:21],byteorder='big')
            if (module1_Requested_state == 2):
                module1_Enable = 2
            else:
                module1_Enable = 1
            module1_Start_possible = int.from_bytes(module1_data[21:22],byteorder='big')
            module1_Stop_possible = int.from_bytes(module1_data[22:23],byteorder='big')
            module1_Reset_possible = int.from_bytes(module1_data[23:24],byteorder='big')
            module1_State = int.from_bytes(module1_data[24:25],byteorder='big')
            if ((module1_State == 2) or (module1_State == 4) or (module1_State == 5) or (module1_State == 9)):
                Module1_Request_start ='00'
            elif(module1_State == 6):
                Module1_Request_stop ='00'
            #module1_Alert = module1_data[25:32]
            #module1_Alertmessage = ''.join(['%02x' % b for b in module1_Alert])
            #module1_Startup_count = (struct.unpack('f',(module1_data[32:36])))[0]
            module1_TotalWattHour = ((struct.unpack('f',module1_data[36:40]))[0])*10
            module1_TotalOperHour = ((struct.unpack('f',module1_data[40:44]))[0])*10
            module1_TotalCycleWatt = ((struct.unpack('f',module1_data[44:48]))[0])*10
            module1_TotalCycleHour = ((struct.unpack('f',module1_data[48:52]))[0])*10
            module1_OutPutPower = (struct.unpack('f',module1_data[52:56]))[0]
            if (module1_OutPutPower < 150 or module1_State == 1):
                module1_OutPutPower = 0
            module1_OutPutVol = (struct.unpack('f',module1_data[56:60]))[0]
            module1_OutPutCur = ((struct.unpack('f',module1_data[60:64]))[0])*10
            module1_StackPower = (struct.unpack('f',module1_data[64:68]))[0]
            module1_StackVol =((struct.unpack('f',module1_data[68:72]))[0])*10
            if module1_StackVol < 0:
                module1_StackVol = 0
            module1_StackCur = ((struct.unpack('f',module1_data[72:76]))[0])*10
            #print(module1_StackCur)
            if module1_StackCur < 0:
                module1_StackCur = 0
            module1_StackTemp = ((struct.unpack('f',module1_data[76:80]))[0])*10
            module1_StackCoolantPre = ((struct.unpack('f',module1_data[80:84]))[0])*10
            module1_effic = (struct.unpack('f',module1_data[84:88]))[0]
            #module1_FC_free_run = int.from_bytes(module1_data[96:97],byteorder='big')
            #module1_Radiator_state = (struct.unpack('f',module1_data[100:104]))[0]
        except:
            print('module1 Get data error')
        #-------------------------------------------------------------------------------------
          
        #------------------module2 data-------------------------------------------------------
        """try:
            module2_data = get_module2_data(module2_IP)
            module2_Requested_state = int.from_bytes(module2_data[20:21],byteorder='big')
            if (module2_Requested_state == 2):
                module2_Enable = 2
            else:
                module2_Enable = 1
            module2_Start_possible = int.from_bytes(module2_data[21:22],byteorder='big')
            module2_Stop_possible = int.from_bytes(module2_data[22:23],byteorder='big')
            module2_Reset_possible = int.from_bytes(module2_data[23:24],byteorder='big')
            module2_State = int.from_bytes(module2_data[24:25],byteorder='big')
            if ((module2_State == 2) or (module2_State == 4) or (module2_State == 5) or (module2_State == 9)):
                Module2_Request_start ='00'
            elif(module2_State == 6):
                Module2_Request_stop ='00'
            #module2_Alert = module2_data[25:32]
            #module2_Alertmessage = ''.join(['%02x' % b for b in module2_Alert])
            #module2_Startup_count = (struct.unpack('f',(module2_data[32:36])))[0]
            module2_TotalWattHour = ((struct.unpack('f',module2_data[36:40]))[0])*10
            module2_TotalOperHour = ((struct.unpack('f',module2_data[40:44]))[0])*10
            module2_TotalCycleWatt = ((struct.unpack('f',module2_data[44:48]))[0])*10
            module2_TotalCycleHour = ((struct.unpack('f',module2_data[48:52]))[0])*10
            module2_OutPutPower = (struct.unpack('f',module2_data[52:56]))[0]
            if (module2_OutPutPower < 0 or module2_State == 1):
                module2_OutPutPower = 0
            module2_OutPutVol = ((struct.unpack('f',module2_data[56:60]))[0])*10
            module2_OutPutCur = ((struct.unpack('f',module2_data[60:64]))[0])*10
            module2_StackPower = (struct.unpack('f',module2_data[64:68]))[0]
            module2_StackVol =((struct.unpack('f',module2_data[68:72]))[0])*10
            if module2_StackVol < 0:
                module2_StackVol = 0
            module2_StackCur = ((struct.unpack('f',module2_data[72:76]))[0])*10
            if (module2_StackCur <= 0):
                module2_StackCur = 0
            module2_StackTemp = ((struct.unpack('f',module2_data[76:80]))[0])*10
            module2_StackCoolantPre = ((struct.unpack('f',module2_data[80:84]))[0])*10
            module2_effic = (struct.unpack('f',module2_data[84:88]))[0]
            #module2_FC_free_run = int.from_bytes(module2_data[96:97],byteorder='big')
            #module2_Radiator_state = (struct.unpack('f',module2_data[100:104]))[0]
        except:
            print('module2 Get data error')
        """
        #----------------------------------------------------------------------------------------
    
        #------------------module3 data-------------------------------------------------------
        try:
            module3_data = get_module3_data(module3_IP)
            module3_Requested_state = int.from_bytes(module3_data[20:21],byteorder='big')
            if (module3_Requested_state == 2):
                module3_Enable = 2
            else:
                module3_Enable = 1
            module3_Start_possible = int.from_bytes(module3_data[21:22],byteorder='big')
            module3_Stop_possible = int.from_bytes(module3_data[22:23],byteorder='big')
            module3_Reset_possible = int.from_bytes(module3_data[23:24],byteorder='big')
            module3_State = int.from_bytes(module3_data[24:25],byteorder='big')
            if ((module3_State == 2) or (module3_State == 4) or (module3_State == 5) or (module3_State == 9)):
                Module3_Request_start ='00'
            elif(module3_State == 6):
                Module3_Request_stop ='00'
            #module3_Alert = module3_data[25:32]
            #module3_Alertmessage = ''.join(['%02x' % b for b in module3_Alert])
            #module3_Startup_count = (struct.unpack('f',(module3_data[32:36])))[0]
            module3_TotalWattHour = ((struct.unpack('f',module3_data[36:40]))[0])*10
            module3_TotalOperHour = ((struct.unpack('f',module3_data[40:44]))[0])*10
            module3_TotalCycleWatt = ((struct.unpack('f',module3_data[44:48]))[0])*10
            module3_TotalCycleHour = ((struct.unpack('f',module3_data[48:52]))[0])*10
            module3_OutPutPower = (struct.unpack('f',module3_data[52:56]))[0]
            if (module3_OutPutPower < 0):
                module3_OutPutPower = 0
            module3_OutPutVol = ((struct.unpack('f',module3_data[56:60]))[0])*10
            module3_OutPutCur = ((struct.unpack('f',module3_data[60:64]))[0])*10
            module3_StackPower = (struct.unpack('f',module3_data[64:68]))[0]
            module3_StackVol = ((struct.unpack('f',module3_data[68:72]))[0])*10
            module3_StackCur = ((struct.unpack('f',module3_data[72:76]))[0])*10
            if (module3_StackCur <= 0):
                module3_StackCur = 0
            module3_StackTemp = ((struct.unpack('f',module3_data[76:80]))[0])*10
            module3_StackCoolantPre = ((struct.unpack('f',module3_data[80:84]))[0])*10
            module3_effic = (struct.unpack('f',module3_data[84:88]))[0]
            #module3_FC_free_run = int.from_bytes(module3_data[96:97],byteorder='big')
            #module3_Radiator_state = (struct.unpack('f',module3_data[100:104]))[0]
        except:
            print('module3 Get data error')
        #----------------------------------------------------------------------------------------
        
            #handleFANspeed()
        ModuleState = str(module1_State) +str(0) + str(module3_State)
        ModuleTotalOutPut = module1_OutPutPower + module3_OutPutPower #+ module3_OutPutPower
        #print(ModuleTotalOutPut)
        TotalkW = module1_TotalWattHour + module3_TotalWattHour #+ module3_TotalWattHour
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
            module3_State == 3 or module3_State == 4 or module3_State == 5 or module3_State == 6 or module3_State == 2 or module3_State == 9 ):
            #module2_State == 3 or module2_State == 4 or module2_State == 5 or module2_State == 6 or module2_State == 2 or module2_State == 9):
            GPIO.output(FuelPumControl, GPIO.HIGH)
            SysRunTimeStart = time.time()
            if (SysRunTimeStart - SysRunTimeStop >= 3600):
                SysRunTime = SysRunTime + 1
                SysRunTimeStop = time.time()
        else:
            GPIO.output(FuelPumControl, GPIO.LOW)
        fuelConsume = ((module1_effic * module1_OutPutPower) * 0.9) + ((module3_effic * module3_OutPutPower) * 0.9) #+ ((module2_effic * module2_OutPutPower) * 0.9)
        fuelConsume = fuelConsume * 0.1
        #print(fuelConsume)
#         if (module1_State == 8 or module2_State == 8 or leaksensor1 >= 1 or OutPutVol <= 2950 or T1 > 700 or T2 > 500 or FuelLevel <=0):# or module3_State == 8):
#             if (inTI - SendGmailTi >= 7200):
#                 #ModuleErrorSendGmail()
#                 SendGmailTi = time.time()
        
        if (sysAuto == 1):
            print("Hello")
            if (inTI - SetCMDTi >= 1):
                if (abs(ModuleTotalOutPut - sysOutPut) <= 50):
                    module1_CurSet = module1_CurSet
                    #module2_CurSet = module2_CurSet
                    module3_CurSet = module3_CurSet
                elif (ModuleTotalOutPut <= sysOutPut):
                    module1_CurSet = module1_CurSet + 1
                    #module2_CurSet = module2_CurSet + 1
                    module3_CurSet = module3_CurSet + 1
                    SetCMDTi = time.time()
                elif(ModuleTotalOutPut <= sysOutPut):
                    module1_CurSet = module1_CurSet - 1
                    #module2_CurSet = module2_CurSet - 1
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
                        #'FC2V':module2_StackVol,
                        #'FC2A':module2_StackCur,
                        #'FC2T':module2_StackTemp,
                        #'FC2P':module2_StackCoolantPre,
                        'FC1AC':module1_TotalWattHour,
                        'FC1OA':module1_OutPutCur,
                        'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                        'A0200':sysOutPut,
                        'FC1TI':module1_TotalOperHour,
                        #'FC2AC':module2_TotalWattHour,
                        #'FC2TI':module2_TotalOperHour,
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
                        #'FC2OA':module2_OutPutCur,
                        'FC1OW':module1_OutPutPower,
                        #'FC2OW':module2_OutPutPower,
                        'FC1SC':module1_TotalCycleHour,
                        #'FC2SC':module2_TotalCycleHour,
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
                        #'FC2H':module2,
                        'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                        'lastTI':int(dataLasTI),
                        'sysRT':SysRunTime,
                        'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                        #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                        'FC3H':module3,
                        'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)}
                    upload = requests.post(url,json = dataupload)
                    Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                    DBsave.commit()
                    #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                    #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
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
                        #'FC2V':module2_StackVol,
                        #'FC2A':module2_StackCur,
                        #'FC2T':module2_StackTemp,
                        #'FC2P':module2_StackCoolantPre,
                        'FC1AC':module1_TotalWattHour,
                        'FC1OA':module1_OutPutCur,
                        'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                        'A0200':sysOutPut,
                        'FC1TI':module1_TotalOperHour,
                        #'FC2AC':module2_TotalWattHour,
                        #'FC2TI':module2_TotalOperHour,
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
                        #'FC2OA':module2_OutPutCur,
                        'FC1OW':module1_OutPutPower,
                        #'FC2OW':module2_OutPutPower,
                        'FC1SC':module1_TotalCycleHour,
                        #'FC2SC':module2_TotalCycleHour,
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
                        #'FC2H':module2,
                        'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                        'lastTI':int(dataLasTI),
                        'sysRT':SysRunTime,
                        'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                        #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                        'FC3H':module3,
                        'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)}
                    upload = requests.post(url,json = dataupload)
                    Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                    DBsave.commit()
                    #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                    #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
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
                        #'FC2V':module2_StackVol,
                        #'FC2A':module2_StackCur,
                        #'FC2T':module2_StackTemp,
                        #'FC2P':module2_StackCoolantPre,
                        'FC1AC':module1_TotalWattHour,
                        'FC1OA':module1_OutPutCur,
                        'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                        'A0200':sysOutPut,
                        'FC1TI':module1_TotalOperHour,
                        #'FC2AC':module2_TotalWattHour,
                        #'FC2TI':module2_TotalOperHour,
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
                        #'FC2OA':module2_OutPutCur,
                        'FC1OW':module1_OutPutPower,
                        #'FC2OW':module2_OutPutPower,
                        'FC1SC':module1_TotalCycleHour,
                        #'FC2SC':module2_TotalCycleHour,
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
                        #'FC2H':module2,
                        'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                        'lastTI':int(dataLasTI),
                        'sysRT':SysRunTime,
                        'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                        #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                        'FC3H':module3,
                        'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)}
                    upload = requests.post(url,json = dataupload)
                    Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                    DBsave.commit()
                    #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                    #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
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
                        #'FC2V':module2_StackVol,
                        #'FC2A':module2_StackCur,
                        #'FC2T':module2_StackTemp,
                        #'FC2P':module2_StackCoolantPre,
                        'FC1AC':module1_TotalWattHour,
                        'FC1OA':module1_OutPutCur,
                        'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                        'A0200':sysOutPut,
                        'FC1TI':module1_TotalOperHour,
                        #'FC2AC':module2_TotalWattHour,
                        #'FC2TI':module2_TotalOperHour,
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
                        #'FC2OA':module2_OutPutCur,
                        'FC1OW':module1_OutPutPower,
                        #'FC2OW':module2_OutPutPower,
                        'FC1SC':module1_TotalCycleHour,
                        #'FC2SC':module2_TotalCycleHour,
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
                        #'FC2H':module2,
                        'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                        'lastTI':int(dataLasTI),
                        'sysRT':SysRunTime,
                        'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                        #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                        'FC3H':module3,
                        'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)}
                    upload = requests.post(url,json = dataupload)
                    Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                    DBsave.commit()
                    #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                    #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
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
                        #'FC2V':module2_StackVol,
                        #'FC2A':module2_StackCur,
                        #'FC2T':module2_StackTemp,
                        #'FC2P':module2_StackCoolantPre,
                        'FC1AC':module1_TotalWattHour,
                        'FC1OA':module1_OutPutCur,
                        'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                        'A0200':sysOutPut,
                        'FC1TI':module1_TotalOperHour,
                        #'FC2AC':module2_TotalWattHour,
                        #'FC2TI':module2_TotalOperHour,
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
                        #'FC2OA':module2_OutPutCur,
                        'FC1OW':module1_OutPutPower,
                        #'FC2OW':module2_OutPutPower,
                        'FC1SC':module1_TotalCycleHour,
                        #'FC2SC':module2_TotalCycleHour,
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
                        #'FC2H':module2,
                        'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                        'lastTI':int(dataLasTI),
                        'sysRT':SysRunTime,
                        'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                        #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                        'FC3H':module3,
                        'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)}
                    upload = requests.post(url,json = dataupload)
                    Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                    DBsave.commit()
                    #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                    #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
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
                ModuleState = str(module1_State) + str(0) + str(module3_State)
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
                        #'FC2V':module2_StackVol,
                        #'FC2A':module2_StackCur,
                        #'FC2T':module2_StackTemp,
                        #'FC2P':module2_StackCoolantPre,
                        'FC1AC':module1_TotalWattHour,
                        'FC1OA':module1_OutPutCur,
                        'SYSPCTRL':'%s:%s'%(sysAuto,sysOutPut),
                        'A0200':sysOutPut,
                        'FC1TI':module1_TotalOperHour,
                        #'FC2AC':module2_TotalWattHour,
                        #'FC2TI':module2_TotalOperHour,
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
                        #'FC2OA':module2_OutPutCur,
                        'FC1OW':module1_OutPutPower,
                        #'FC2OW':module2_OutPutPower,
                        'FC1SC':module1_TotalCycleHour,
                        #'FC2SC':module2_TotalCycleHour,
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
                        #'FC2H':module2,
                        'SPEC':'%s|%s:%s'%('A0201','-5000','6000'),
                        'lastTI':int(dataLasTI),
                        'sysRT':SysRunTime,
                        'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                        #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
                        'FC3H':module3,
                        'FC3CTRL':'%s|%s'%(module3_Enable,module3_CurSet)}
                upload = requests.post(url,json = dataupload)
                Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                DBsave.commit()
                #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
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
                    #'A1001':fuelConsume,
                    'FC1A':module1_StackCur,
                    'FC1T':module1_StackTemp,
                    'FC1P':module1_StackCoolantPre,
                    #'FC2V':module2_StackVol,
                    #'FC2A':module2_StackCur,
                    #'FC2T':module2_StackTemp,
                    #'FC2P':module2_StackCoolantPre,
                    'FC1AC':module1_TotalWattHour,
                    'FC1OA':module1_OutPutCur,
                    'FC1TI':module1_TotalOperHour,
                    #'FC2AC':module2_TotalWattHour,
                    #'FC2TI':module2_TotalOperHour,
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
                    #'FC2OA':module2_OutPutCur,
                    'FC1OW':module1_OutPutPower,
                    #'FC2OW':module2_OutPutPower,
                    'FC1SC':module1_TotalCycleHour,
                    #'FC2SC':module2_TotalCycleHour,
                    'FCC':3,'TA':OutPutCur,
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
                    #'FC2H':module2,
                    'sysRT':SysRunTime,
                    'FC1CTRL':'%s|%s'%(module1_Enable,module1_CurSet),
                    #'FC2CTRL':'%s|%s'%(module2_Enable,module2_CurSet),
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
                
                #print(dataupload)
                upload = requests.post(url,json = dataupload)
                Cursor.execute("insert into Sysdata values (?, ?, ?)", (inTI,RM,SysRunTime))
                DBsave.commit()
                #RMpayload = {'api_key': writeAPIkey, 'field1':RM,'field2':SysRunTime}
                #RMupload = requests.post('https://api.thingspeak.com/update', params=RMpayload)
                print((time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),upload.text))
                print(RM)
                #print(int(SOC))
                #print(dataupload)
                #print(OutPutVol)
                #print(dataupload)
                #print(int(FuelLevel))
            except:
                print('Data Upload ERROR')


        if (OutPutVol < 3000): #Situation 1: Without charging load. Consume power normally.int(SOC) < 4 and OutPutWat <= 7000
            print("Situiation 1: Without charging load. Consume power normally")
            SetCMD = 1
            if (SetCMD == 1):
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
#         print(LastTI - inTI)
#      except:
#         print('Internet Error')


