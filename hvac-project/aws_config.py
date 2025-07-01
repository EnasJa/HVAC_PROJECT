# aws_config.py
# הגדרות חיבור ל-AWS IoT Core

import os

# נתיב לתעודות
CERT_PATH = "certificates/"

# קבצי תעודות ך
DEVICE_CERT = CERT_PATH + "f8fbd121f6948294287ed70d32c9d18493a2e1b64b56b8c5071b538d026b905d-certificate.pem.crt"
PRIVATE_KEY = CERT_PATH + "f8fbd121f6948294287ed70d32c9d18493a2e1b64b56b8c5071b538d026b905d-private.pem.key"
ROOT_CA = CERT_PATH + "AmazonRootCA1.pem"

# נקודת הגישה של AWS IoT 
AWS_IOT_ENDPOINT = "a1ipqemsvgkjmp-ats.iot.us-east-1.amazonaws.com"

# הגדרות MQTT
MQTT_PORT = 8883
CLIENT_ID = "hvac-building-sensor"

# נושאי MQTT
MQTT_TOPICS = {
    "sensors": "hvac/building/sensors",
    "status": "hvac/building/status",
    "alerts": "hvac/building/alerts"
}