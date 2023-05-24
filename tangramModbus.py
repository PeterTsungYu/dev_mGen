import serial
import struct

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
    # Slave ID (1byte) | Func code (1byte) | Starting Address (2byte) | Number of Data Entry (2byte) | Number of Data in Bytes (2byte) | Data Entries (2byte) | CRC (2byte)
    num_entries = len(data)
    num_bytes = num_entries * 2  # Each entry is 2 bytes

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
        packet.extend(struct.pack('>H', entry))

    packet.extend(calculate_crc16(packet))

    return packet

