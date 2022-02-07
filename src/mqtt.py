import paho.mqtt.client as paho
from paho import mqtt

import config

def on_connect(client, userdata, flags, rc, properties=None):
  print("🟢 MQTT connected received with code %s." % rc)

def on_connect_fail(client, userdata, flags, rc, properties=None):
  print("🔴 MQTT failed received with code %s." % rc)

def on_publish(client, userdata, mid, properties=None):
  print('🚀 On publish 🚀')
  client.disconnect()

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
  pass

def on_message(client, userdata, msg):
  pass

def initializeMQTT():
  client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
  client.on_connect = on_connect

  client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

  client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

  client.connect(config.MQTT_HOST, int(config.MQTT_PORT))

  client.on_subscribe = on_subscribe
  client.on_message = on_message
  client.on_publish = on_publish
  client.on_connect_fail = on_connect_fail

  return client
