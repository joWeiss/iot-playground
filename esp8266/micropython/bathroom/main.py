import machine
import time
from umqtt.simple import MQTTClient

from config import *

PIN_R = 12
PIN_G = 13
PIN_B = 14


class RGBLed:
    def __init__(self, pin_r, pin_g, pin_b):
        self.pin_r = machine.PWM(machine.Pin(pin_r))
        self.pin_g = machine.PWM(machine.Pin(pin_g))
        self.pin_b = machine.PWM(machine.Pin(pin_b))
        self.set(0, 0, 0)
        self.state = 1

    def switch_on(self):
        self.state = 1
        self.set(255, 0, 0)

    def switch_off(self):
        self.state = 0
        self.set(0, 0, 0)

    def set_color(self, color):
        if self.state:
            if color == "green":
                self.set(0, 255, 0)
            elif color == "red":
                self.set(255, 0, 0)

    def set(self, r, g, b):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        self.duty()

    def duty(self):
        self.pin_r.duty(self.duty_translate(self.r))
        self.pin_g.duty(self.duty_translate(self.g))
        self.pin_b.duty(self.duty_translate(self.b))

    def duty_translate(self, n):
        """translate values from 0-255 to 0-1023"""
        return int((float(n) / 255) * 1023)


class PhotoCell:
    def __init__(self):
        self.sensor = machine.ADC(0)

    def read(self):
        return self.sensor.read()

    def is_dark(self):
        return self.read() < 100


class MqttClient:
    def __init__(self, client_id, host, port, user=None, password=None):
        self.client = MQTTClient(
            client_id, host, port=port, user=user, password=password
        )
        self.client.set_callback(self.sub_cb)
        self.client.connect()

    def subscribe(self, topic):
        self.client.subscribe(topic.encode())

    def sub_cb(self, topic, msg):
        topic = topic.decode("utf-8").lower()
        msg = msg.decode("utf-8").lower()
        if topic == "klo/switch":
            global led
            if msg == "on":
                led.switch_on()
            elif msg == "off":
                led.switch_off()

    def check_msg(self):
        self.client.check_msg()
        time.sleep_ms(100)

    def publish(self, topic, msg):
        self.client.publish(topic, msg.encode())


led = RGBLed(PIN_R, PIN_G, PIN_B)
light_sensor = PhotoCell()
mqtt_client = MqttClient(
    "esp8266-12e",
    MQTT_HOST,
    port=MQTT_PORT,
    user=MQTT_USER,
    password=MQTT_PASS,
)
mqtt_client.subscribe("klo/switch")

occupied = 1

while True:
    mqtt_client.check_msg()
    if light_sensor.is_dark() and occupied:
        occupied = 0
        led.set_color("green")
        mqtt_client.publish("klo/state", "0")
    elif not light_sensor.is_dark():
        if not occupied:
            occupied = 1
            led.set_color("red")
            mqtt_client.publish("klo/state", "1")
