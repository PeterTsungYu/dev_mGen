import time
import json
from datetime import datetime
import threading
import mqttModule

class sysModule:
    def __init__(self, id:str, lst_servers:list):
        self.id = id
        self.lst_servers = lst_servers
        self.sink_connector = mqttModule.MQTT_client()
        self.client_threads = []
        self.thread_timeout = 10
        self.stop_threads = False
    
    def data_factory_sink_connector(self,):
        self.sink_connector.start_client_threads()

        while not self.stop_threads:
            for server in self.lst_servers:
                for key, value in server.data_silo.items():
                    msg = {"metadata": {"sys_id": self.id, "id": key}, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    msg.update(value)
                    self.sink_connector.client.publish("test_topic", json.dumps(msg), qos=2, retain=False)
                    print("Published mqtt message:", msg)
            time.sleep(self.threading_timeout)

    def start_client_threads(self,):
        thread = threading.Thread(target=self.data_factory_sink_connector, name=f'data_factory_sink_connector',)
        thread.start()
        self.client_threads.append(thread)

    def stop_client_threads(self,):
        self.stop_threads = True
        # Close all client sockets
        for client_thread in self.client_threads:
            client_thread.join()
        self.client_threads = []