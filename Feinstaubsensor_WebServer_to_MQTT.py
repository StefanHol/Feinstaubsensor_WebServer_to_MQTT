#!/usr/bin/env python3
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


# add to crontab after reboot
# crontab -e
# @reboot  /home/pi/start_MQTTWebServer.sh


from http.server import HTTPServer, BaseHTTPRequestHandler
# from optparse import OptionParser
import paho.mqtt.client as mqtt
import json
import logging
from logging.handlers import RotatingFileHandler

class myHTTP_2_MQTT_Pushlisher():
    def __init__(self, MQTT):
        ############################################
        # Edit HTTP Server Port and IP here
        ############################################
        port = 8080
        IP = '127.0.0.1'
        try:
            server = HTTPServer((IP, port), RequestHandler)
            server.mqtt = MQTT
            server.mqtt.app_log.info('Listening HTTP on %s:%s' % (IP, port))
            server.serve_forever()
        except Exception as e:
            MQTT.app_log.error("Error: starting HTTP Server: %s, IP: %s, Port: %s" %(e, IP, port) )
            exit()

class main():
    def __init__(self):
        ############################################
        # Edit MQTT Server Port, IP, ID and PW here
        ############################################
        mqttServer = "127.0.0.1"
        mqttUserId = ""
        mqttPassword = ""
        mqttPort = 1883

        ############################################
        # Edit Luftsensor ID or edit multiple IDs
        ############################################
        AllowedIDs = ['1234567', '7654321']
        Prefix = "tele"
        Topic = "luftsensor_"
        # Complete Topic:
        # >>> tele/luftsensor_<SensorID>/<Parameter> Value
        app_log = self.log()
        self.mqttH = mqttHandler(mqttServer, mqttUserId, mqttPassword, mqttPort, AllowedIDs, Prefix, Topic, app_log)
        self.server = myHTTP_2_MQTT_Pushlisher(self.mqttH)

    def log(self):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

        logFile = 'log.log'

        logging_file_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5 * 1024 * 1024,
                                         backupCount=2, encoding=None, delay=0)
        logging_file_handler.setFormatter(log_formatter)
        logging_file_handler.setLevel(logging.INFO)

        app_log = logging.getLogger('root')
        app_log.setLevel(logging.INFO)

        app_log.addHandler(logging_file_handler)
        return app_log

class RequestHandler(BaseHTTPRequestHandler):

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
        # self.read_all_data_from_sensor(self.format_data(data))
        self.server.mqtt.HTTP_2_MQTT(data)
        # self.server.mqtt.app_log.info("Content Length: %s" % (length))
        # self.server.mqtt.app_log.info("Request headers: %s" % (request_headers))
        # self.server.mqtt.app_log.info("Request payload: %s" % self.rfile.read(length))

        # print("Content Length:", length)
        # print("Request headers:", request_headers)
        # print("Request payload:", self.rfile.read(length))
        # print("<----- Request End -----\n")

        self.send_response(200)
        self.end_headers()

    do_PUT = do_POST
    do_DELETE = do_GET

    def push_data(self, data_str):
        self.server.mqtt.app_log.info("def push_data(): %s" %(str(data_str)))
        pass


class mqttHandler():
    def __init__(self, mqttServer, mqttUserId, mqttPassword, mqttPort, AllowedIDs, Prefix, Topic, app_log):
        self.mqttServer = mqttServer
        self.mqttUserId = mqttUserId
        self.mqttPassword = mqttPassword
        self.mqttPort = mqttPort

        self.AllowedIDs = AllowedIDs
        self.Prefix = Prefix
        self.Topic = Topic

        self.app_log = app_log

        self.TopicAndPrefix = self.Prefix + "/" + self.Topic
        self.init_mqtt()

    def init_mqtt(self):
        # print("init_mqtt")
        self.mqttc = mqtt.Client()
        try:
            self.mqttc.username_pw_set(self.mqttUserId, self.mqttPassword)
            self.mqttc.connect(self.mqttServer, self.mqttPort)
            self.mqttc.loop_start()
            self.app_log.info('Connected to MQTT-Broker on %s:%s' % (self.mqttServer, self.mqttPort))
        except Exception as e:
            self.app_log.error("Error: connecting mqtt Server: %s" %(e) )


    def mqttPublish(self, Topic, Value):
        # Publish to MQTT server
        # print("mqttPublish", Topic, Value)
        self.mqttc.publish(Topic, Value)

    def read_all_data_from_sensor(self, parsed_json):
        # print("read_all_data_from_sensor", parsed_json)
        try:

            esp8266id = parsed_json["esp8266id"]
            if esp8266id in self.AllowedIDs:
                # self.app_log.info("Known esp8266id:   ", esp8266id)
                for each in parsed_json['sensordatavalues']:
                    if "pressure" in str(each['value_type']):
                        # preassure data of BME280 have to be divided by 100
                        self.app_log.info(str(each['value_type']) + " " + str(float(each['value']) / 100))
                        Value = float(each['value']) / 100
                    else:
                        self.app_log.info(str(each['value_type']) + " " + str(each['value']))
                        Value = each['value']
                    Topic = self.TopicAndPrefix + str(esp8266id) + "/" + each['value_type']

                    ######################################################
                    ######################################################
                    self.mqttPublish(Topic, Value)
                    ######################################################
                    ######################################################
            else:
                self.app_log.warning("Ignore unknown ID: %s" % str(esp8266id))
        except Exception as e:
            self.app_log.error("error in read_all_data_from_sensor: %s" %(e))

    def format_data(self, data):
        try:
            parsed_json = json.loads(data.decode().replace("'", '"'))
            # print(type(data))
            # print(type(parsed_json))
            # print("extract_data . ", parsed_json)
            return parsed_json
        except Exception as e:
            self.app_log.error("Error converting JSON DATA: %s" %(e))
            return {}

    def HTTP_2_MQTT(self, data):
        self.app_log.info("HTTP_2_MQTT: %s" %(data))
        self.read_all_data_from_sensor(self.format_data(data))
        pass


if __name__ == "__main__":
    # parser = OptionParser()
    # parser.usage = ("Creates an http-server that will echo out any GET or POST parameters\n"
    #                 "Run:\n\n"
    #                 "   reflect")
    # (options, args) = parser.parse_args()

    m = main()