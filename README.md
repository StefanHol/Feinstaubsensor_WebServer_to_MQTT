# Feinstaubsensor_WebServer_to_MQTT

Create simple HTTP Server to receive Data from Sensors (https://luftdaten.info) and Publish these data separated for each value to your MQTT-Broker

# Requirement
- Build your own sensor. See at https://luftdaten.info

# install python3 requirements on rasbpian
- install python3 (on raspbian it is installed by default)
- install pip & mqtt for python3
- sudo apt-get update
- sudo apt-get install python3-pip
- pip3 install paho-mqtt

# Sensor Configuration
- Log in into your sensor
- enable "Send to own API"
- ![Sensor Configuration](img/SensorConfig.png?raw=true "Sensor Configuration")

# Server Configuration
- modify HTTP Server IP & Port
- modify MQTT Server IP, Port, User & PW
- modify the Topic
- Sensor IF will be a part of the Topic

# Test the Server
- python3 Feinstaubsensor_WebServer_to_MQTT.py
- ctrl + c to stop server
## using script to run server
- make the Script executable
- chmod +x start_MQTTWebServer.sh
- now run start_MQTTWebServer.sh
- sh ./start_MQTTWebServer.sh
- ![incoming mqtt data](img/mqtt_data.png?raw=true "incoming mqtt data")

# add script to startup
- crontab -e
- add these line
- @reboot <pathToYourScript>/start_MQTTWebServer.sh
- e.g.
- @reboot  /home/pi/start_MQTTWebServer.sh

