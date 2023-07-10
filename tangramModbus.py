import serial
import struct
import threading


def calculate_crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    # return as a 2 bytes hexadecimal value, it is in a reverse order (byteorder='little')
    return crc.to_bytes(2, byteorder='little')


class tangramModbus_slave:
    def __init__(self, slave_ID=1, serial_port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.slave_ID = slave_ID
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout
        self.register_data = []
        # Create the serial connection
        ## timeout=1, Set a read timeout value in seconds
        self.ser = serial.Serial(self.serial_port, self.baudrate, self.timeout)
        # Flag to indicate whether the Modbus thread should stop
        self.stop_modbus_thread = False
        # global var for data storage. Get updaated from the main program.
        self.modbus_packet = bytearray()
        self.lst_thread = []

    def create_modbus_slave_packet(self, function_code:int, data=[], starting_add=0, register_number=0, byte_count=0):
        self.modbus_packet = bytearray()
        # append as a single byte (0-255)
        self.modbus_packet.append(self.slave_ID)
        self.modbus_packet.append(function_code)

        if starting_add != 0: # starting address arror
            self.modbus_packet.append(2)
        elif register_number != 30: # number of register error
            self.modbus_packet.append(3)
        else:
            if function_code == 3: # Read multiple slave's registers
            # Slave ID (1byte) | Func code (1byte) | Number of Data in Bytes (2byte) | Data Entries (2byte each) | CRC (2byte)
                # extend with another bytearray to the packet
                ## struct pack returns a 2 byte (0-65535) array by default for each entry
                ## H specifies that the data should be packed as an unsigned short integer (2 bytes)
                ## > indicates that the data should be formatted in big-endian byte order (normal order). This means that the most significant byte comes first in the resulting binary representation.
                ## For example, let's say entry is an integer with a value of 258 (0x0102 in hexadecimal). The corresponding packed binary data will be b'\x01\x02', where \x01 represents the most significant byte (1) and \x02 represents the least significant byte (2).
                num_entries = len(data)
                num_bytes = num_entries * 4  # Each entry is 2 bytes
                self.modbus_packet.extend(struct.pack('>H', num_bytes))
                for entry in data:
                    # 'I'/'i', for 4bytes. 'I' for unsigned integer. 'i' for signed integer.
                    # 'H'/'h', for 2bytes. 'H' for unsigned integer. 'h' for signed integer.
                    # unsigned: 0~65535. signed: -32768~32767
                    # 'f' for 4bytes float type. Range: ±3.4 x 10^38
                    # print(entry)
                    self.modbus_packet.extend(struct.pack('>f', float(entry)))
            elif function_code == 16: # Write to multiple slave's registers
            # Slave ID (1byte) | Func code (1byte) | Starting addr (2byte) | Number of Registers (2byte) | CRC (2byte)
                self.modbus_packet.extend(struct.pack('>HH', starting_add, register_number))
            else: # func code error
                self.modbus_packet.append(1)

        self.modbus_packet.extend(calculate_crc16(self.modbus_packet))

        return self.modbus_packet

    # Function to continuously read Modbus messages
    def handle_modbus_master_msg(self):
        while not self.stop_modbus_thread:
            # Check if any character is available to read
            if self.ser.in_waiting >= 0:
                # Read the available bytes from the serial port
                msg = self.ser.read(self.ser.in_waiting).decode()
                # Extract the slave ID (1 byte)
                slave_id = int(msg[0], 16)
                # Extract the function code (1 byte)
                function_code = int(msg[1], 16)

                if slave_id == self.slave_ID:
                    if function_code == 3: # Read from multiple registers
                        # Extract the starting address (2 bytes)
                        starting_add = struct.unpack('>H', msg[2:4])[0]
                        # Extract the number of registers (2 bytes)
                        register_number = struct.unpack('>H', msg[4:6])[0]
                    elif function_code == 16: #Write to multiple registers
                        # Extract the starting address (2 bytes)
                        starting_add = struct.unpack('>H', msg[2:4])[0]
                        # Extract the number of registers (2 bytes)
                        register_number = struct.unpack('>H', msg[4:6])[0]
                        # Extract the byte counts (2 bytes)
                        byte_count = struct.unpack('>H', msg[6:8])[0]
                    
                    self.create_modbus_slave_packet(function_code=function_code, data=self.register_data, starting_add=starting_add, register_number=register_number, byte_count=byte_count)
                    self.ser.write(self.modbus_packet)
                    print("Slave write modbus_packet")
                    return self.modbus_packet
                else:
                    print("Unsupported Slave ID")
                    return None
        
        # Close the serial connection
        self.ser.close()
    
    def dynamic_start_thread(self, method_name, method_args):
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            thread = threading.Thread(target=method, name=method_name, args=method_args)
            thread.start()
            self.lst_thread.append(thread)
        else:
            print(f"Method '{method_name}' not found")
    
    def dynamic_stop_thread(self,):
        pass
        