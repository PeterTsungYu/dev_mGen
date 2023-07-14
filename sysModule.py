import time
import json
from datetime import datetime
import threading
import requests
import ssl
from dotenv import load_dotenv
import os
import mqttModule

# Load environment variables from .env file
load_dotenv()

# Access environment variables
VM_IP = os.getenv("VM_IP")
sys_id = os.getenv("sys_id")
mongodb_remote_conn_url = os.getenv("mongodb_remote_conn_url")
mongodb_remote_database = os.getenv("mongodb_remote_database")
mongodb_remote_collection = os.getenv("mongodb_remote_collection")

class sysModule:
    def __init__(self, lst_servers:list, id=sys_id):
        self.id = id
        self.lst_servers = lst_servers
        self.lst_mqtt_topics = self.init_lst_mqtt_topics()
        self.update_mqtt_source_json()
        self.update_mongodb_sink_json()
        self.sink_connector = mqttModule.MQTT_connector(lst_sub_topics=self.lst_mqtt_topics)
        self.client_threads = []
        self.thread_timeout = 10
        self.stop_threads = False
    
    def init_lst_mqtt_topics(self,):
        _lst_mqtt_topics = []
        for server in self.lst_servers:
            for key in server.data_silo.keys():
                _lst_mqtt_topics.append(key)
        return _lst_mqtt_topics
    
    def update_mqtt_source_json(self,):
        mqtt_source = { "name": "mqtt-source",
                       "config": {
                           "connector.class": "io.confluent.connect.mqtt.MqttSourceConnector",
                           "tasks.max": "1",
                           "mqtt.server.uri":  "tcp://remote-mqtt-broker:1883",
                           "mqtt.topics": self.lst_mqtt_topics,
                           "kafka.topic": self.id,
                           "value.converter":"org.apache.kafka.connect.converters.ByteArrayConverter",
                           "confluent.topic.bootstrap.servers": "broker:29092",
                           "confluent.license": "",
                           "topic.creation.enable": True,
                           "topic.creation.default.replication.factor": -1,
                           "topic.creation.default.partitions": -1 
                           }} 
        
        with open('mqtt-source.json', 'w') as f:
            json.dump(mqtt_source, f)
        
        url = f'http://{VM_IP}:8083/connectors' 
        headers = {'Content-Type': 'application/json'}
        # read the data in as a string
        data = open('mqtt-source.json', 'r').read()
        # response = requests.get(url)
        # use data arg to pass json-string to the post request 
        response = requests.post(url, headers=headers, data=data)
        print(response.status_code)
        print(response.text)
        # TODO: #7 Handle response
        if response.status_code == 201:
            pass
    
    def update_mongodb_sink_json(self,):
        mongodb_sink = { "name": "mongodb-sink",
                        "config": {
                            "connector.class":"com.mongodb.kafka.connect.MongoSinkConnector",
                            "tasks.max":1,
                            "topics": self.id,
                            "connection.uri":mongodb_remote_conn_url,
                            "database":mongodb_remote_database,
                            "collection":mongodb_remote_collection,
                            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
                            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
                            "value.converter.schemas.enable":"false",
                            "consumer.auto.offset.reset": "latest",
                            "offset.storage.topic": "connect-offsets",
                            "timeseries.timefield":"timestamp",
                            "timeseries.timefield.auto.convert":"true",
                            "timeseries.timefield.auto.convert.date.format":"yyyy-MM-dd HH:mm:ss",
                            "transforms": "RenameField,InsertTopic",
                            "transforms.RenameField.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
                            "transforms.RenameField.renames": "h:humidity, p:pressure, t:temperature",
                            "transforms.InsertTopic.type":"org.apache.kafka.connect.transforms.InsertField$Value",
                            "transforms.InsertTopic.topic.field":"Source_topic"
                            }}
        
        with open('mongodb-sink.json', 'w') as f:
            json.dump(mongodb_sink, f)
        
        url = f'http://{VM_IP}:8083/connectors' 
        headers = {'Content-Type': 'application/json'}
        # read the data in as a string
        data = open('mongodb-sink.json', 'r').read()
        # response = requests.get(url)
        # use data arg to pass json-string to the post request 
        response = requests.post(url, headers=headers, data=data)
        print(response.status_code)
        print(response.text)
        # TODO: #8 Handle response
        if response.status_code == 201:
            pass
    
    def data_factory_sink_connector(self,):
        self.sink_connector.start_client_threads()

        while not self.stop_threads:
            for server in self.lst_servers:
                for key, value in server.data_silo.items():
                    msg = {"metadata": {"sys_id": self.id, "id": key}, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    msg.update(value)
                    self.sink_connector.client.publish(key, json.dumps(msg), qos=2, retain=False)
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