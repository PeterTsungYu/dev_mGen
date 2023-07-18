# dev_mGen (Still under development)
In this project, the main system and sub-systems are controlled by an embedded microcontroller. 
To better maintain and develop a control strategy, the main program is programmed in an object-oriented fashion.
We use Python as our language to represent real-world objects in virtual modules.

## Sub-Servers
Every sub-server contains a class definition to define a class that is used to act as a server of their clients.
Take h35kModule for example, there are 1-3 real-world fuel cell modules installed in the system.
Each fuel cell module is a client to communicate with a server that is defined in the sub-module Pythonic class.

Within class attributes, there are several attributes including "client_threads" and "data_silo".
There are also class methods that are used to "collect_client_data_silos", "start_client_threads", and "stop_client_threads".
As you can see, the threading strategy is applied, which means each server has its own thread for each client in a non-blocking fashion. 

Below is a list of sub-servers and their corresponding clients:
- h35kModule.py: A fuel cell module that defines classes of a server and a client.
   - h35kModule_client 
- raspModule.py: A Raspberry Pi 3B+ as the microcontroller. It opens the port for RS485 Modbus protocols, serial ports, and GPIOs.
  - batmeterModule.py: A load meter to measure the power data of a battery rack.
  - fuelLevelModule.py: A level sensor to measure the liquid level of a fuel tank.
  - loadmeterModule.py: A load meter to measure the power data of the system.
  - pvModule.py: A PV module.
  - tempModule.py: A temperature measuring board to collect data from temperature sensors.


## Main Server
The main server collects data silos from sub-servers. After organizing the data, it will then be piped to a local database or a data streaming platform.
- sysModule.py
  - h35kModule.py
  - raspModule.py
  - mqttModule.py: An MQTT client to pub/sub to topics. It will then deliver data to a data streaming platform.
  - sysMongodb.py: An MongoDB client to read/write data to a local MongoDB database.

