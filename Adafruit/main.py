# main.py -- put your code here!

import time                   # Allows use of time.sleep() for delays
from mqtt import MQTTClient   # For use of MQTT protocol to talk to Adafruit IO
import ubinascii              # Conversions between binary data and various encodings
import machine                # Interfaces with hardware components
import micropython            # Needed to run any MicroPython code
import random                 # Random number generator
from machine import Pin       # Define pin
import dht


# BEGIN SETTINGS
# These need to be change to suit your environment
RANDOMS_INTERVAL = 20000    # milliseconds
last_random_sent_ticks = 0  # milliseconds
led = Pin("LED", Pin.OUT)   # led pin initialization for Raspberry Pi Pico W

# Wireless network
WIFI_SSID = "Asus_Guest_2.4G"
WIFI_PASS = "Tq7mNauK*tK86K5$Gr!V" # No this is not our regular password. :)

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "Samiie"
AIO_KEY = "aio_mVDD87ohrC2SgWVeMATyIsZPXIUQ"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_TEMP_FEED = "Samiie/feeds/temp"
AIO_HUM_FEED = "Samiie/feeds/moist"

# END SETTINGS
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
    print((topic, msg))          # Outputs the message that was received. Debugging use.
    if msg == b"ON":             # If message says "ON" ...
        led.on()                 # ... then LED on
    elif msg == b"OFF":          # If message says "OFF" ...
        led.off()                # ... then LED off
    else:                        # If any other message is received ...
        print("Unknown message") # ... do nothing but output that it happened.


# FUNCTIONS

# Function to connect Pico to the WiFi
def do_connect():
    import network
    from time import sleep
    import machine
    wlan = network.WLAN(network.STA_IF)         # Put modem on Station mode

    if not wlan.isconnected():                  # Check if already connected
        print('connecting to network...')
        wlan.active(True)                       # Activate network interface
        # set power mode to get WiFi power-saving off (if needed)
        wlan.config(pm = 0xa11140)
        wlan.connect("WIFI_SSID", "WIFI_PASS")  # Your WiFi Credential
        print('Waiting for connection...', end='')
        # Check if it is connected otherwise wait
        while not wlan.isconnected() and wlan.status() >= 0:
            print('.', end='')
            sleep(1)
    # Print the IP assigned by router
    ip = wlan.ifconfig()[0]
    print('\nConnected on {}'.format(ip))
    return ip 


# Function to publish random number to Adafruit IO MQTT server at fixed interval
def send_random():

    tempSensor.measure()
    temperature = tempSensor.temperature()
    humidity = tempSensor.humidity()
    print("Temperature is {} degrees Celsius and Humidity is {}%".format(temperature, humidity))
    
    print("Publishing: {0} to {1} ... ".format(temperature, AIO_TEMP_FEED), end='')
    print("Publishing: {0} to {1} ... ".format(humidity, AIO_HUM_FEED), end='')
    try:
        client.publish(topic=AIO_TEMP_FEED, msg=str(temperature))
        client.publish(topic=AIO_HUM_FEED, msg=str(humidity))
        print("DONE")
    except Exception as e:
        print("FAILED")
    time.sleep(15)


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
client.subscribe(AIO_TEMP_FEED)
client.subscribe(AIO_HUM_FEED)
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_TEMP_FEED))
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_HUM_FEED))



try:                      # Code between try: and finally: may cause an error
                        # so ensure the client disconnects the server if
    
    tempSensor = dht.DHT11(machine.Pin(27))                    # that happens.
    while 1:              # Repeat this loop forever
        client.check_msg()# Action a message if one is received. Non-blocking.
        send_random()     # Send a random number to Adafruit IO if it's time.
finally:                  # If an exception is thrown ...
    client.disconnect()   # ... disconnect the client and clean up.
    client = None
    print("Disconnected from Adafruit IO.")