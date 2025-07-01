# hvac_aws_simulator.py
# HVAC Simulator connecting to AWS IoT Core - Updated Version

import json
import time
import random
import datetime
import ssl
import paho.mqtt.client as mqtt
from aws_config import *

class HVACAWSSimulator:
    def __init__(self):
        # 4 building zones
        self.zones = ["lobby", "office_floor_1", "office_floor_2", "conference_room"]
        self.client = None
        self.connected = False
        self.messages_sent = 0
        self.retry_count = 0
        self.max_retries = 5
        
        print("🏢 HVAC AWS IoT System Ready!")
        print(f"🔗 Connecting to: {AWS_IOT_ENDPOINT}")
    
    def setup_mqtt_client(self):
        """Setup MQTT client with AWS certificates"""
        try:
            # Create MQTT client with new API
            self.client = mqtt.Client(
                client_id=CLIENT_ID,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            
            # Setup SSL/TLS
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Load certificates
            context.load_verify_locations(ROOT_CA)
            context.load_cert_chain(DEVICE_CERT, PRIVATE_KEY)
            
            # Set TLS context
            self.client.tls_set_context(context)
            
            # Setup callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up MQTT client: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Connection callback"""
        if rc == 0:
            self.connected = True
            self.retry_count = 0  # Reset retry count on successful connection
            print("✅ Successfully connected to AWS IoT Core!")
            print(f"📡 Client ID: {CLIENT_ID}")
        else:
            print(f"❌ Connection failed with code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc, reason_code=None, properties=None):
        """Disconnect callback"""
        self.connected = False
        print("🔌 Disconnected from AWS IoT Core")
        if rc != 0:
            print(f"⚠️ Unexpected disconnection. Return code: {rc}")
            if reason_code:
                print(f"📋 Reason: {reason_code}")
    
    def on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        """Message publish callback"""
        self.messages_sent += 1
        print(f"📤 Message {self.messages_sent} sent (ID: {mid})")
    
    def connect_to_aws(self):
        """Connect to AWS IoT Core with retry logic"""
        if not self.setup_mqtt_client():
            return False
        
        while self.retry_count < self.max_retries:
            try:
                print(f"🔄 Attempting to connect to AWS IoT Core... (Attempt {self.retry_count + 1}/{self.max_retries})")
                self.client.connect(AWS_IOT_ENDPOINT, MQTT_PORT, 60)
                self.client.loop_start()
                
                # Wait for connection
                timeout = 10
                while not self.connected and timeout > 0:
                    time.sleep(1)
                    timeout -= 1
                
                if self.connected:
                    print("🎉 Connection successful!")
                    return True
                else:
                    self.retry_count += 1
                    if self.retry_count < self.max_retries:
                        wait_time = min(5 * self.retry_count, 30)  # Exponential backoff
                        print(f"⏰ Connection timeout. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    
            except Exception as e:
                self.retry_count += 1
                print(f"❌ Connection error: {e}")
                if self.retry_count < self.max_retries:
                    wait_time = min(5 * self.retry_count, 30)
                    print(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        print(f"❌ Failed to connect after {self.max_retries} attempts")
        return False
    
    def generate_sensor_data(self, zone_id):
        """Generate sensor data for a zone"""
        # More realistic temperature variations based on zone
        base_temps = {
            "lobby": 22.0,
            "office_floor_1": 23.0,
            "office_floor_2": 22.5,
            "conference_room": 21.5
        }
        
        base_temp = base_temps.get(zone_id, 22.0)
        temp = round(base_temp + random.uniform(-2, 3), 1)
        humidity = round(random.uniform(40, 60), 1)
        co2 = random.randint(400, 1200)
        
        # Calculate air quality
        if co2 < 600:
            air_quality = "excellent"
        elif co2 < 800:
            air_quality = "good"
        elif co2 < 1000:
            air_quality = "moderate"
        else:
            air_quality = "poor"
        
        # HVAC status based on conditions
        if temp > 25 or co2 > 1000:
            hvac_status = "cooling_high"
        elif temp < 20:
            hvac_status = "heating"
        elif temp > 24:
            hvac_status = "cooling_low"
        else:
            hvac_status = "auto"
        
        return {
            "device_id": f"hvac-sensor-{zone_id}",
            "zone_id": zone_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "temperature_celsius": temp,
            "humidity_percent": humidity,
            "co2_ppm": co2,
            "air_quality": air_quality,
            "hvac_status": hvac_status,
            "building_id": "smart-office-tlv"
        }
    
    def publish_sensor_data(self, data):
        """Send data to AWS IoT"""
        if not self.connected:
            print("❌ Not connected to AWS")
            return False
        
        try:
            topic = f"{MQTT_TOPICS['sensors']}/{data['zone_id']}"
            payload = json.dumps(data, ensure_ascii=False)
            
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            else:
                print(f"❌ Publish error: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Publish exception: {e}")
            return False
    
    def run_simulation(self, duration_minutes=10, interval_seconds=30):
        """Run the simulation"""
        print(f"🚀 Starting simulation for {duration_minutes} minutes")
        print(f"⏱️  Send interval: {interval_seconds} seconds")
        print("=" * 70)
        
        # Connect to AWS
        if not self.connect_to_aws():
            print("❌ Cannot connect to AWS. Stopping simulation.")
            return
        
        try:
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)
            failed_publishes = 0
            
            while datetime.datetime.now() < end_time:
                if not self.connected:
                    print("⚠️ Connection lost. Attempting to reconnect...")
                    if not self.connect_to_aws():
                        print("❌ Reconnection failed. Stopping simulation.")
                        break
                
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"\n⏰ {current_time}")
                print("-" * 70)
                
                # Send data from all zones
                for zone in self.zones:
                    data = self.generate_sensor_data(zone)
                    
                    # Local display
                    status_emoji = {
                        "excellent": "🟢",
                        "good": "🟡", 
                        "moderate": "🟠",
                        "poor": "🔴"
                    }
                    
                    hvac_emoji = {
                        "cooling_high": "❄️❄️",
                        "cooling_low": "❄️",
                        "heating": "🔥",
                        "auto": "🌡️"
                    }
                    
                    emoji = status_emoji.get(data["air_quality"], "⚪")
                    hvac_status_emoji = hvac_emoji.get(data["hvac_status"], "🌡️")
                    
                    print(f"{emoji} {zone}: "
                          f"🌡️ {data['temperature_celsius']}°C | "
                          f"💧 {data['humidity_percent']}% | "
                          f"🫁 {data['co2_ppm']} PPM | "
                          f"{hvac_status_emoji} {data['hvac_status']}")
                    
                    # Send to AWS
                    if self.publish_sensor_data(data):
                        print(f"  ✅ Sent to AWS: hvac/building/sensors/{zone}")
                        failed_publishes = 0  # Reset failed counter
                    else:
                        failed_publishes += 1
                        print(f"  ❌ Failed to send to AWS")
                        
                        # If too many failed publishes, try to reconnect
                        if failed_publishes >= 3:
                            print("⚠️ Multiple publish failures. Attempting to reconnect...")
                            self.connected = False
                            failed_publishes = 0
                    
                    time.sleep(1)  # Small delay between zones
                
                # Summary
                print(f"\n📊 Total messages sent: {self.messages_sent}")
                print(f"🔗 Connection status: {'✅ Connected' if self.connected else '❌ Disconnected'}")
                
                # Wait for next cycle
                print(f"⏳ Waiting {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n⏹️ Simulation stopped by user")
            
        finally:
            if self.client:
                print("🔌 Disconnecting from AWS IoT Core...")
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except Exception as e:
                    print(f"⚠️ Error during disconnect: {e}")
            
            print(f"\n📈 Final Statistics:")
            print(f"📤 Total messages sent: {self.messages_sent}")
            print(f"🏢 Zones monitored: {len(self.zones)}")
            print("✅ Simulation complete!")

def main():
    """Main function"""
    print("🚀 Starting HVAC Simulator with AWS IoT Core")
    print("=" * 70)
    
    # Check certificate files
    import os
    
    required_files = [DEVICE_CERT, PRIVATE_KEY, ROOT_CA]
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing certificate files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("💡 Make sure you copied all certificate files to certificates/ folder")
        return
    
    print("✅ All certificate files found")
    
    # Create and run simulator
    simulator = HVACAWSSimulator()
    
    # Run simulation for longer duration with shorter intervals
    simulator.run_simulation(duration_minutes=10, interval_seconds=20)

if __name__ == "__main__":
    main()