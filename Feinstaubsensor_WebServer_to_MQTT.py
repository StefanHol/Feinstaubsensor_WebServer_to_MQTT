#!/usr/bin/env python
# Written by Stefan Holstein
#
# Luftsensor Daten separiert über mqtt weiterleiten
# Luftsensor -> ThisServer -> MQTTBroker
#
#
#
# thanks to Nathan Hamiel (2010)
# # https://gist.github.com/huyng/814831
# and thanks to
# # https://stackoverflow.com/a/30288641/9722867
#
#
# sudo apt-get update
# for python3 use:
# sudo apt-get install python3-pip
# pip3 install paho-mqtt
# or
# for python2 use
# sudo apt-get install python-pip
# pip install paho-mqtt

# create Script start_MQTTWebServer.sh
# #!/bin/sh
# sleep 10
# python3 Feinstaubsensor_WebServer_to_MQTT.py &


# add to crontab afer reboot
# crontab -e
# @reboot  /home/pi/start_MQTTWebServer.sh


from http.server import HTTPServer, BaseHTTPRequestHandler
# from optparse import OptionParser
import paho.mqtt.client as mqtt
import json

class myHTTP_2_MQTT_Pushlisher():
    def __init__(self, MQTT):
        ############################################
        # Edit HTTP Server Port and IP here
        ############################################
        port = 8089
        IP = '192.168.1.100'
        print('Listening HTTP on %s:%s' % (IP, port))
        server = HTTPServer((IP, port), RequestHandler)
        server.mqtt = MQTT
        server.serve_forever()

class main():
    def __init__(self):
        ############################################
        # Edit MQTT Server Port, IP, ID and PW here
        ############################################
        mqttServer = "192.168.1.100"
        mqttUserId = ""
        mqttPassword = ""
        mqttPort = 1883

        print('Publish MQTT on %s:%s' % (mqttServer, mqttPort))

        self.mqttH = mqttHandler(mqttServer, mqttUserId, mqttPassword, mqttPort)
        self.server = myHTTP_2_MQTT_Pushlisher(self.mqttH)

class RequestHandler(BaseHTTPRequestHandler):
    ############################################
    # Edit Luftsensor ID or edit multiple IDs
    ############################################
    AllowedIDs = ['1234567', '7654321']
    Prefix = "tele"
    Topic = "luftsensor_"
    TopicAndPrefix = Prefix + "/" + Topic

    def do_GET(self):
        request_path = self.path
        self.push_data(request_path)

        # print("\n----- Request Start ----->\n")
        # print("Request path:", request_path)
        # print("Request headers:", self.headers)
        # print("<----- Request End -----\n")

        self.send_response(200)
        self.send_header("Set-Cookie", "foo=bar")
        self.end_headers()

    def do_POST(self):
        request_path = self.path

        # print("\n----- Request Start ----->\n")
        # print("Request path:", request_path)

        request_headers = self.headers
        content_length = request_headers.get('Content-Length')
        length = int(content_length) if content_length else 0

        data = self.rfile.read(length)
        self.read_all_data_from_sensor(self.format_data(data))

        # print("Content Length:", length)
        # print("Request headers:", request_headers)
        # print("Request payload:", self.rfile.read(length))
        # print("<----- Request End -----\n")

        self.send_response(200)
        self.end_headers()

    do_PUT = do_POST
    do_DELETE = do_GET

    def push_data(self, data_str):
        print("def push_data():", str(data_str))
        pass

    def read_all_data_from_sensor(self, parsed_json):
        # print("read_all_data_from_sensor", parsed_json)
        try:

            esp8266id = parsed_json["esp8266id"]
            if esp8266id in self.AllowedIDs:
                # print("Known esp8266id:   ", esp8266id)
                for each in parsed_json['sensordatavalues']:
                    if "pressure" in str(each['value_type']):
                        # preassure data of BME280 have to be divided by 100
                        print(each['value_type'], float(each['value']) / 100)
                        Value = float(each['value']) / 100
                    else:
                        print(each['value_type'], each['value'])
                        Value = each['value']
                    Topic = self.TopicAndPrefix + str(esp8266id) + "/" + each['value_type']

                    ######################################################
                    ######################################################
                    self.server.mqtt.mqttPublish(Topic, Value)
                    ######################################################
                    ######################################################
            else:
                print("Ignore unknown ID: ", esp8266id)
        except:
            print("error in read_all_data_from_sensor")

    def format_data(self, data):
        try:
            parsed_json = json.loads(data.decode().replace("'", '"'))
            # print(type(data))
            # print(type(parsed_json))
            # print("extract_data . ", parsed_json)
            return parsed_json
        except:
            print("Error converting JSON DATA")
            return {}

class mqttHandler():
    def __init__(self, mqttServer, mqttUserId, mqttPassword, mqttPort):
        self.mqttServer = mqttServer
        self.mqttUserId = mqttUserId
        self.mqttPassword = mqttPassword
        self.mqttPort = mqttPort
        self.init_mqtt()

    def init_mqtt(self):
        # print("init_mqtt")
        self.mqttc = mqtt.Client()
        self.mqttc.username_pw_set(self.mqttUserId, self.mqttPassword)
        self.mqttc.connect(self.mqttServer, self.mqttPort)
        self.mqttc.loop_start()

    def mqttPublish(self, Topic, Value):
        # Publish to MQTT server
        self.mqttc.publish(Topic, Value)


if __name__ == "__main__":
    # parser = OptionParser()
    # parser.usage = ("Creates an http-server that will echo out any GET or POST parameters\n"
    #                 "Run:\n\n"
    #                 "   reflect")
    # (options, args) = parser.parse_args()

    m = main()