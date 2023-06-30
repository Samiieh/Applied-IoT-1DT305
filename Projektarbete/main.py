from machine import ADC,Pin
from mqtt import MQTTClient  
import time
import machine
import ubinascii
import network
import secret
import utime


# Define the relay pins
relay_pin1 = Pin(1, Pin.OUT)
relay_pin2 = Pin(2, Pin.OUT)

# Function to activate relay_pin1 and deactivate relay_pin2
def relay_high():
    relay_pin1.on()
    relay_pin2.off()

# Function to activate relay_pin2 and deactivate relay_pin1
def relay_low():
    relay_pin1.off()
    relay_pin2.on()

# Function to deactivate both relay pins
def relay_off():
    relay_pin1.off()
    relay_pin2.off()

#fuktsensor config
soil = ADC(Pin(27)) 

min_moisture=0
max_moisture=65535

readDelay = 15

def soil_sensor():
    moisture = (max_moisture - soil.read_u16()) * 130 / (max_moisture - min_moisture)
    print("moisture: " + "%.2f" % moisture + "% (adc: " + str(soil.read_u16()) + ")")
    utime.sleep(readDelay)

    # Publish the soil moisture value to AIO_SOIL_FEED
    client.publish(AIO_SOIL_FEED, str(moisture))
    
    

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "Samiie"
AIO_KEY = "aio_mVDD87ohrC2SgWVeMATyIsZPXIUQ"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id()).decode()  # Can be anything
AIO_TOGGLE_FEED = "Samiie/feeds/toggle"
AIO_SOIL_FEED = "Samiie/feeds/soil-moist"

# Callback function to handle subscribed messages
def sub_cb(topic, msg):
    if topic.decode() == AIO_TOGGLE_FEED:
        if msg.decode() == "ON":
            relay_high()
        elif msg.decode() == "OFF":
            relay_low()

# Function to connect Pico to the WiFi
def do_connect():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.active(True)
        wlan.connect(secret.WIFI_SSID, secret.WIFI_PASS)
        while not wlan.isconnected():
            pass
    ip = wlan.ifconfig()[0]
    print('\nConnected on {}'.format(ip))
    return ip

# Try WiFi Connection
try:
    ip = do_connect()
except KeyboardInterrupt:
    print("Keyboard interrupt")

# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)

# Subscribed messages will be delivered to this callback
client.set_callback(sub_cb)
client.connect()
client.subscribe(AIO_TOGGLE_FEED)
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_TOGGLE_FEED))

try:
    while True:
        client.check_msg()
        time.sleep(0.1)
        soil_sensor()
finally:
    client.disconnect()
    print("Disconnected from Adafruit IO.")