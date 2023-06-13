import paho.mqtt.client as paho
# from paho import mqtt
import time

# Define MQTT broker settings
broker_address = "localhost"
broker_port = 1883
client_id = "local_mqtt_client"

# Define callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT!")
    else:
        print(f"Failed to connect, return code %d\n", rc)
    # Subscribe to a topic upon successful connection
    client.subscribe("test", qos=0)

def on_message(client, userdata, msg):
    print("Received message: " + msg.payload.decode())

# Create a MQTT client instance
client = paho.Client(client_id, clean_session=True)

# Set the callback functions
client.on_connect = on_connect
client.on_message = on_message

# enable TLS for secure connection
# client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# client.username_pw_set("", "peteryo121!@")

# Connect to the MQTT broker
client.connect(broker_address, broker_port, keepalive=60)

# Start the MQTT network loop in a non-blocking manner
client.loop_start()
time.sleep(1)

# Publish and receive messages
for i in range(3):
    message = f"Hello, MQTT {i+1}!"
    client.publish("test", message, qos=2, retain=False)
    print("Published message:", message)

# Disconnect the client
client.loop_stop()
client.disconnect()
