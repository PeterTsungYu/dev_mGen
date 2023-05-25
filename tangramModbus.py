import serial
import struct


# Flag to indicate whether the Modbus thread should stop
stop_modbus_thread = False
# global var for data storage. Get updaated from the main program.
modbus_packet = bytearray()


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


def create_modbus_packet(slave_address, function_code, data):
    global modbus_packet
    # Slave ID (1byte) | Func code (1byte) | Starting Address (2byte) | Number of Data Entry (2byte) | Number of Data in Bytes (2byte) | Data Entries (2byte) | CRC (2byte)
    num_entries = len(data)
    num_bytes = num_entries * 4  # Each entry is 2 bytes

    packet = bytearray()
    # append as a single byte (0-255)
    packet.append(slave_address)
    packet.append(function_code)
    # extend with another bytearray to the packet
    ## struct pack returns a 2 byte (0-65535) array by default for each entry
    ## H specifies that the data should be packed as an unsigned short integer (2 bytes)
    ## > indicates that the data should be formatted in big-endian byte order (normal order). This means that the most significant byte comes first in the resulting binary representation.
    ## For example, let's say entry is an integer with a value of 258 (0x0102 in hexadecimal). The corresponding packed binary data will be b'\x01\x02', where \x01 represents the most significant byte (1) and \x02 represents the least significant byte (2).
    packet.extend(struct.pack('>HHH', 0, num_entries, num_bytes))

    for entry in data:
        # 'I'/'i', for 4bytes. 'I' for unsigned integer. 'i' for signed integer.
        # 'H'/'h', for 2bytes. 'H' for unsigned integer. 'h' for signed integer.
        # unsigned: 0~65535. signed: -32768~32767
        # 'f' for 4bytes float type. Range: ±3.4 x 10^38
        # print(entry)
        packet.extend(struct.pack('>f', float(entry)))

    packet.extend(calculate_crc16(packet))

    modbus_packet = packet
    return packet


# Function to continuously read Modbus messages
def handle_modbus_message(slave_address, function_code, data):
    # Create the serial connection
    ## timeout=1, Set a read timeout value in seconds
    ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)

    while not stop_modbus_thread:
        # Check if at least one character is available to read
        if ser.in_waiting >= 16:
            # Read the available bytes from the serial port
            data = ser.read(ser.in_waiting).decode()
            if data == "01100000002E4015":
                ser.write(modbus_packet)
    
    # Close the serial connection
    ser.close()
