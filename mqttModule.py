import paho.mqtt.client as paho
# from paho import mqtt
import threading

class MQTT_connector:
    def __init__(self, lst_sub_topics:list, broker_address="localhost", broker_port=1883, client_id="local_mqtt_client",):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client_id = client_id
        self.lst_sub_topics = lst_sub_topics
        self.client = self.instantiate(self.lst_sub_topics)
        self.client_threads = []
        self.stop_threads = False


    def instantiate(self, lst_sub_topics:list):
        # Define callback functions
        def on_connect(self, client, userdata, flags, rc):
            if rc == 0:
                print(f"Connected to MQTT!")
            else:
                print(f"Failed to connect, return code %d\n", rc)
            # Subscribe to a topic upon successful connection
            for topic in lst_sub_topics:
                self.client.subscribe(topic, qos=0)

        def on_message(self, client, userdata, msg):
            print("Received message: " + msg.payload.decode())

        # Create a MQTT client instance
        client = paho.Client(self.client_id, clean_session=True)

        # Set the callback functions
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        # enable TLS for secure connection
        # client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        # client.username_pw_set("", "peteryo121!@")
        return client

    def mqtt_thread(self,):
        # Connect to the MQTT broker
        self.client.connect_async(self.broker_address, self.broker_port, keepalive=60)

        # Start the MQTT network loop in a non-blocking manner
        self.client.loop_start()
        while not self.stop_threads:
            pass

        # Disconnect the client
        self.client.loop_stop()
        self.client.disconnect()
        print("close connection to MQTT broker")
    
    def start_client_threads(self,):
        thread = threading.Thread(target=self.mqtt_thread, name=f'mqtt_thread',)
        thread.start()
        self.client_threads.append(thread)

    def stop_client_threads(self,):
        self.stop_threads = True
        # Close all client sockets
        for client_thread in self.client_threads:
            client_thread.join()
        self.client_threads = []