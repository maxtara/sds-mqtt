# SDS-MQTT
  
## Description
Simple docker image for the SDS011 air quality sensor, which publishes the data to MQTT as JSON.
The JSON can be easily read by homeassistant.
  
Most of the code is from [here](https://gist.github.com/kadamski/92653913a53baf9dd1a8). I converted it to python3 pretty haphazardly, and added the MQTT/JSON part.
  
It runs every 10 minutes, and collects 5 measurements, publishing the last one to MQTT (I assume to push some air through the sensor).

  
## Docker-compose
```
  sds-mqtt:
    container_name: maxtara/sds-mqtt
    image: sds-mqtt
    restart: unless-stopped
    devices:
        - /dev/ttyUSB0
    environment:
      MQTT_HOST: '192.168.1.1'
      MQTT_PASSWORD: "password"
      MQTT_USERNAME: 'user'
      MQTT_PORT: "1883"
      MQTT_TOPIC: 'home/pmsensor/main'
      SERIAL_PORT: "/dev/ttyUSB0"
```
  
## Homeassistant config
```
  - platform: mqtt
    name: "pm25 Inside"
    state_topic: "home/pmsensor/main"
    unit_of_measurement: 'µg/m3'
    value_template: "{{ value_json.pm25 }}"
    force_update: true
  - platform: mqtt
    name: "pm10 Inside"
    state_topic: "home/pmsensor/main"
    unit_of_measurement: 'µg/m3'
    value_template: "{{ value_json.pm10 }}"
    force_update: true
```

## Build
```
docker build -t sds-mqtt .
# Deploy
docker tag sds-mqtt maxtara/sds-mqtt:latest
docker push maxtara/sds-mqtt
``` 