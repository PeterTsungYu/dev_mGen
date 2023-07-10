import struct
import socket
import time
import threading

# TCP/UDP Client, in this project, it should be a H35K module
class h35kModule_client:
    def __init__(self, id:str, ip:str, mac_addr:str, TCPport=44818, UDPport=2222,):
        self.id = id
        self.ip = ip
        self.mac_addr = mac_addr
        # port opens on device
        self.TCPport = TCPport
        self.UDPport = UDPport
        self.state = 0
        self.totalWattHour = 0
        self.totalOperHour = 0
        self.totalCycleWatt = 0
        self.totalCycleHour = 0
        self.outputPower = 0
        self.outputVol = 0
        self.outputCur = 0            
        self.stackPower = 0
        self.stackVol = 0
        self.stackCur = 0
        self.stackTemp = 0
        self.stackCoolantPre = 0
        self.effic = 0
        # module output current set 15A
        # 5000W / 320V ~= 15A
        self.curSet_highest = 15
    
    def module_data_populate(self, module_data):
        '''
        Populate module data from received data
        '''
        try:
            self.state = int.from_bytes(module_data[24:25],byteorder='big')
            self.totalWattHour = ((struct.unpack('f',module_data[36:40]))[0])*10
            self.totalOperHour = ((struct.unpack('f',module_data[40:44]))[0])*10
            self.totalCycleWatt = ((struct.unpack('f',module_data[44:48]))[0])*10
            self.totalCycleHour = ((struct.unpack('f',module_data[48:52]))[0])*10
            self.outputPower = (struct.unpack('f',module_data[52:56]))[0]
            self.outputVol = (struct.unpack('f',module_data[56:60]))[0]
            self.outputCur = ((struct.unpack('f',module_data[60:64]))[0])*10
            self.stackPower = (struct.unpack('f',module_data[64:68]))[0]
            self.stackVol = ((struct.unpack('f',module_data[68:72]))[0])*10
            self.stackCur = ((struct.unpack('f',module_data[72:76]))[0])*10
            self.stackTemp = ((struct.unpack('f',module_data[76:80]))[0])*10
            self.stackCoolantPre = ((struct.unpack('f',module_data[80:84]))[0])*10
            self.effic = (struct.unpack('f',module_data[84:88]))[0]
            print(f'module_data_populate of {self.id} succeeds')
        except Exception as e:
            print('module_data_populate error:' +  str(e))
        

# TCP/UDP Server, in this project, it should be a control board, i.e. Rpi
class h35kModule_server:
    def __init__(self, lst_clients:list, ip='0.0.0.0'):
        self.ip = ip
        # port opens on device
        self.lst_TCPport = [49200,49201,49202]
        self.lst_UDPport = [49200,49201,49202]
        self.lst_clients = lst_clients
        self.clients_output_msg = self.init_clients_output_msg()
        self.clients_socket = self.init_clients_socket()
        self.client_threads = []
        # Flag to indicate whether threads should stop
        self.stop_client_threads = False
    
    def init_clients_output_msg(self,):
        assert len(self.lst_clients) <= 3
        msg = {}
        for client in self.lst_clients:
            msg[client.id] = {
                'module_enable': '01',
                'request_Start': '00',
                'request_Stop': '00',
                'request_Reset': '00',
                # module output current set 4A, initial
                'curSet': 4
            }
        return msg
    
    def init_clients_socket(self,):
        assert len(self.lst_clients) <= 3
        module = {}
        for i in range(len(self.lst_clients)):
            try:
                TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                TCP.bind((self.ip, self.lst_TCPport[i]))
                TCP.listen(1)
                TCP.connect((self.lst_clients[i].ip, self.lst_clients[i].TCPport))

                module[self.lst_clients[i].id] = {
                    'TCP':TCP
                }
            except Exception as e:
                print('init_clients_socket_TCP error:' +  str(e))
        return module

    # EthernertIP load data from device
    def TCP_get_module_data(self, client):
        TCP = self.clients_socket[client.id]['TCP']
        while not self.stop_client_threads:
            try:
                # get session number from client
                _register =  bytes.fromhex('65000400000000000000000000000000000000000000000001000000')
                TCP.send(_register)
                _msg = TCP.recv(1024)
                if len(_msg) >= 8:
                    session = _msg[4:8].hex()
                else:
                    raise ValueError("TCP session wrong value")
                
                # get module id and check if it is matched?
                identity = bytes.fromhex('%s%s%s'%('6f001600',session,'00000000000000000000000000000000000000000000020000000000b2000600010220012401'))
                TCP.send(identity)
                _msg = TCP.recv(1024)
                id_1 = _msg[54:55].hex()
                id_2 = _msg[55:56].hex()
                moduleID = int((id_2 + id_1),base=16)
                if str(moduleID) != client.id:
                    raise ValueError("TCP moduleID mismatched")

                # prepare for sending module CMD
                forwardOpen = bytes.fromhex('%s%s%s'%('6f004000',session,'00000000000000000000000000000000000000000000020000000000b20030005402200624010a0a0200550e0300550e550edafa0df0ad8b00000000c0c300002e46c0c300007a40010320042c702c64'))
                forwardClose = bytes.fromhex('%s%s%s'%('6f002800',session,'00000000000000000000000000000000000000000000020000000000b20018004e02200624010a0a550edafa0df0ad8b030020042c702c64'))
                # diff between previous module
                # Module3_ForwardOpen = bytes.fromhex('%s%s%s'%('6f004000',Module3_Session,'00000000000000000000000000000000000000000000020000000000b20030005402200624010a0a02004c6103004c614c61dafa0df0ad8b00000000c0c300002e46c0c300007a40010320042c702c64'))
                # Module3_ForwardClose = bytes.fromhex('%s%s%s'%('6f002800',Module3_Session,'00000000000000000000000000000000000000000000020000000000b20018004e02200624010a0a4c61dafa0df0ad8b030020042c702c64'))
                _Seq = '00000000'
                _CIPSeq = '0000'

                moduleCMD = ''
                for key, value in self.clients_output_msg[client.id].items():
                    if key == 'curSet':
                        value = ''.join(['%02x' % b for b in struct.pack('f', value)])
                    moduleCMD += value
                moduleCMD = moduleCMD + '0000000000000000000000000000000000000000000000000000000000000000'

                TCP.send(forwardOpen)
                _msg = TCP.recv(1024)
                _O2TID = _msg[44:48].hex()
                _T2OID = _msg[48:52].hex()
                
                _O2T = bytes.fromhex('%s%s%s%s%s%s%s'%('020002800800',
                                                        _O2TID,
                                                        _Seq,
                                                        'b1002e00',
                                                        _CIPSeq,
                                                        '01000000',
                                                        moduleCMD
                                                        ))
                TCP.send(_O2T)
                module_data = TCP.recv(1024) 
                
                TCP.send(forwardClose)
                _msg = TCP.recv(1024)
            except socket.timeout as e:
                module_data = None
                print('Module TCP Timeout:' +  str(e))
            except ValueError as ve:
                # Handle ValueErrors raised within the try block
                print("Module TCP ValueError:", str(ve))
            except Exception as e:
                module_data = None    
                print('Module TCP error:' +  str(e))
            TCP.close()
            print('Close TCP connection')

            client.module_data_populate(module_data)
            time.sleep(10)

    def start_TCP_get_module_data_threads(self,):
        for client in self.lst_clients:
            client_thread = threading.Thread(target=self.TCP_get_module_data, args=(client,))
            client_thread.start()
            self.client_threads.append(client_thread)
    
    def stop_client_threads(self,):
        self.stop_client_threads = True
        # Close all client sockets
        for client_thread in self.client_threads:
            client_thread.join()
        self.client_threads = []