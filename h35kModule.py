import struct
import socket

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
        self.outputPower = 0
        self.totalWattHour = 0
        self.effic = 0
        self.totalOperHour = 0
        self.totalCycleWatt = 0
        self.totalCycleHour = 0
        self.outputVol = 0
        self.outputCur = 0            
        self.stackPower = 0
        self.stackVol = 0
        self.stackCur = 0
        self.stackTemp = 0
        self.stackCoolantPre = 0
        # module output current set 15A
        # 5000W / 320V ~= 15A
        self.curSet_highest = 15


# TCP/UDP Server, in this project, it should be a control board, i.e. Rpi
class h35kModule_server:
    def __init__(self, lst_client:list, ip='0.0.0.0'):
        self.ip = ip
        # port opens on device
        self.lst_TCPport = [49200,49201,49202]
        self.lst_UDPport = [49200,49201,49202]
        self.lst_client = lst_client
        self.clients_output_msg = self.init_clients_output_msg()
        self.clients_socket = self.init_clients_socket()
    
    def init_clients_output_msg(self,):
        assert len(self.lst_client) <= 3
        msg = {}
        for client in self.lst_client:
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
        assert len(self.lst_client) <= 3
        module = {}
        for i in range(len(self.lst_client)):
            TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            TCP.bind((self.ip, self.lst_TCPport[i]))
            TCP.listen(1)
            TCP.connect((self.lst_client[i].ip, self.lst_client[i].TCPport))

            module[self.lst_client[i].id] = {
                'TCP':TCP
            }
        return module

    # EthernertIP load data from device
    def TCP_get_module_data(self, client):
        TCP = self.init_clients_socket[client.id]['TCP']

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
        return module_data

        
        


