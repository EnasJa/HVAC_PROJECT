# app.py
# Flask Dashboard for HVAC AWS IoT System

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import threading
import time
from collections import defaultdict, deque
from aws_config import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hvac-dashboard-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class HVACDashboard:
    def __init__(self):
        self.mqtt_client = None
        self.connected = False
        self.sensor_data = defaultdict(lambda: {
            'latest': None,
            'history': deque(maxlen=50)  # Keep last 50 readings
        })
        self.alerts = deque(maxlen=20)  # Keep last 20 alerts
        self.zones = ["lobby", "office_floor_1", "office_floor_2", "conference_room"]
        
        # Statistics
        self.stats = {
            'total_messages': 0,
            'connected_zones': 0,
            'active_alerts': 0,
            'last_update': None
        }
        
        self.setup_mqtt_client()
        self.start_mqtt_connection()
    
    def setup_mqtt_client(self):
        """Setup MQTT client for receiving data"""
        try:
            # Use callback_api_version=2 to fix deprecation warning
            self.mqtt_client = mqtt.Client(
                client_id="hvac-dashboard-receiver",  # Different client ID
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            
            # Setup SSL/TLS
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Load certificates
            context.load_verify_locations(ROOT_CA)
            context.load_cert_chain(DEVICE_CERT, PRIVATE_KEY)
            
            self.mqtt_client.tls_set_context(context)
            
            # Setup callbacks
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.on_log = self.on_log  # Add logging
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up MQTT client: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            print("✅ Dashboard connected to AWS IoT Core!")
            
            # Subscribe to all sensor topics
            for zone in self.zones:
                topic = f"{MQTT_TOPICS['sensors']}/{zone}"
                client.subscribe(topic)
                print(f"📡 Subscribed to: {topic}")
            
            # Emit connection status to web clients
            socketio.emit('connection_status', {'connected': True})
            
        else:
            print(f"❌ Dashboard connection failed: {rc}")
            self.connected = False
            socketio.emit('connection_status', {'connected': False})
    
    def on_disconnect(self, client, userdata, rc, reason_code=None, properties=None):
        """MQTT disconnect callback"""
        self.connected = False
        print("🔌 Dashboard disconnected from AWS IoT Core")
        if reason_code:
            print(f"📋 Disconnect reason: {reason_code}")
        socketio.emit('connection_status', {'connected': False})
    
    def on_log(self, client, userdata, level, buf):
        """Log callback for debugging"""
        if "error" in buf.lower() or "failed" in buf.lower():
            print(f"🔍 MQTT Log: {buf}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming sensor data"""
        try:
            # Parse message
            topic = msg.topic
            payload = msg.payload.decode()
            print(f"🔔 Received message on topic: {topic}")
            print(f"📦 Payload: {payload[:100]}...")  # First 100 chars
            
            data = json.loads(payload)
            zone_id = data.get('zone_id')
            
            if zone_id:
                # Store latest data
                self.sensor_data[zone_id]['latest'] = data
                self.sensor_data[zone_id]['history'].append({
                    'timestamp': data['timestamp'],
                    'temperature': data['temperature_celsius'],
                    'humidity': data['humidity_percent'],
                    'co2': data['co2_ppm']
                })
                
                # Update statistics
                self.stats['total_messages'] += 1
                self.stats['last_update'] = datetime.now().isoformat()
                self.stats['connected_zones'] = len([z for z in self.zones 
                                                   if self.sensor_data[z]['latest']])
                
                # Check for alerts
                self.check_alerts(data)
                
                # Emit to web clients
                try:
                    socketio.emit('sensor_update', {
                        'zone': zone_id,
                        'data': data,
                        'stats': self.stats
                    })
                    print(f"✅ Emitted data to web clients for zone: {zone_id}")
                except Exception as emit_error:
                    print(f"❌ Error emitting to web: {emit_error}")
                
                print(f"📨 Received data from {zone_id}: "
                      f"🌡️{data['temperature_celsius']}°C "
                      f"💧{data['humidity_percent']}% "
                      f"🫁{data['co2_ppm']}ppm")
            else:
                print(f"⚠️ No zone_id in message: {data}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Raw payload: {msg.payload}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            print(f"Topic: {msg.topic}")
            print(f"Payload: {msg.payload}")
    
    def check_alerts(self, data):
        """Check for alert conditions"""
        alerts = []
        zone_id = data['zone_id']
        
        # Temperature alerts
        if data['temperature_celsius'] > 26:
            alerts.append({
                'type': 'temperature_high',
                'zone': zone_id,
                'message': f'High temperature: {data["temperature_celsius"]}°C',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })
        elif data['temperature_celsius'] < 18:
            alerts.append({
                'type': 'temperature_low',
                'zone': zone_id,
                'message': f'Low temperature: {data["temperature_celsius"]}°C',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })
        
        # CO2 alerts
        if data['co2_ppm'] > 1000:
            alerts.append({
                'type': 'co2_high',
                'zone': zone_id,
                'message': f'High CO₂ levels: {data["co2_ppm"]} PPM',
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            })
        
        # Humidity alerts
        if data['humidity_percent'] > 70:
            alerts.append({
                'type': 'humidity_high',
                'zone': zone_id,
                'message': f'High humidity: {data["humidity_percent"]}%',
                'severity': 'info',
                'timestamp': datetime.now().isoformat()
            })
        elif data['humidity_percent'] < 30:
            alerts.append({
                'type': 'humidity_low',
                'zone': zone_id,
                'message': f'Low humidity: {data["humidity_percent"]}%',
                'severity': 'info',
                'timestamp': datetime.now().isoformat()
            })
        
        # Add alerts and emit to clients
        for alert in alerts:
            self.alerts.append(alert)
            socketio.emit('new_alert', alert)
        
        # Update active alerts count
        recent_alerts = [a for a in self.alerts 
                        if datetime.fromisoformat(a['timestamp']) > 
                        datetime.now() - timedelta(minutes=10)]
        self.stats['active_alerts'] = len(recent_alerts)
    
    def start_mqtt_connection(self):
        """Start MQTT connection in background thread"""
        def connect_loop():
            retry_count = 0
            max_retries = 3  # Reduced retries
            
            while True:
                try:
                    if not self.connected and retry_count < max_retries:
                        print(f"🔄 Dashboard connecting to AWS IoT... (Attempt {retry_count + 1}/{max_retries})")
                        
                        # Stop any existing loop
                        try:
                            self.mqtt_client.loop_stop()
                        except:
                            pass
                        
                        # Fresh connection
                        self.mqtt_client.connect(AWS_IOT_ENDPOINT, MQTT_PORT, 60)
                        self.mqtt_client.loop_start()
                        
                        # Wait for connection result
                        timeout = 15
                        while not self.connected and timeout > 0:
                            time.sleep(1)
                            timeout -= 1
                        
                        if self.connected:
                            print("🎉 Dashboard connected successfully!")
                            retry_count = 0  # Reset retry count on successful connection
                            time.sleep(60)   # Check connection every 60 seconds
                        else:
                            retry_count += 1
                            wait_time = 10 * retry_count
                            print(f"⏳ Dashboard connection failed, waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            
                    elif self.connected:
                        time.sleep(60)  # Check connection every 60 seconds
                        retry_count = 0  # Reset retry count when connected
                        
                    else:
                        # Max retries reached, wait longer before trying again
                        print(f"⚠️ Dashboard max retries reached. Waiting 120 seconds...")
                        time.sleep(120)
                        retry_count = 0  # Reset retry count for next cycle
                        
                except Exception as e:
                    print(f"❌ Dashboard connection error: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=connect_loop, daemon=True)
        thread.start()
    
    def get_all_data(self):
        """Get all current sensor data"""
        # Convert deques to lists for JSON serialization
        sensors_data = {}
        for zone, data in self.sensor_data.items():
            sensors_data[zone] = {
                'latest': data['latest'],
                'history': list(data['history'])  # Convert deque to list
            }
        
        return {
            'sensors': sensors_data,
            'alerts': list(self.alerts),  # Convert deque to list
            'stats': self.stats,
            'connected': self.connected
        }

# Initialize dashboard
dashboard = HVACDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint for all data"""
    return jsonify(dashboard.get_all_data())

@app.route('/api/zones')
def get_zones():
    """API endpoint for zones list"""
    return jsonify(dashboard.zones)

@app.route('/api/history/<zone>')
def get_zone_history(zone):
    """API endpoint for zone history"""
    if zone in dashboard.sensor_data:
        return jsonify(list(dashboard.sensor_data[zone]['history']))
    return jsonify([])

@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    print("🔌 New client connected to dashboard")
    emit('initial_data', dashboard.get_all_data())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print("🔌 Client disconnected from dashboard")

@socketio.on('request_data')
def handle_data_request():
    """Handle client data request"""
    emit('initial_data', dashboard.get_all_data())

if __name__ == '__main__':
    print("🚀 Starting HVAC Dashboard Server")
    print("=" * 50)
    print("📊 Dashboard URL: http://localhost:5000")
    print("🔗 Connecting to AWS IoT Core...")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)