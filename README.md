# Smart IoT-based HVAC Monitoring System

**Real-time Environmental Control for Smart Buildings**

A comprehensive IoT-based HVAC monitoring system that leverages AWS cloud infrastructure to provide intelligent building automation with real-time environmental monitoring, predictive alerting, and energy optimization.

## Features

- Real-time environmental monitoring (temperature, humidity, CO2)
- Zone-based control for different building areas  
- Intelligent alerting with automated threshold-based notifications
- Live web dashboard with real-time data visualization
- Serverless AWS architecture for scalability
- Enterprise security with X.509 certificate authentication
- Sub-2 second processing latency
- 100% message delivery success rate during testing

## Architecture

```
IoT Sensors (MQTT/TLS) -> AWS IoT Core -> Lambda + DynamoDB
                                            |
Web Dashboard <- Flask Server (Socket.IO) <-
```

**Technology Stack:**
- Backend: Python 3.8+, Flask, Socket.IO
- Frontend: HTML5, CSS3, JavaScript, Chart.js
- Cloud: AWS IoT Core, Lambda, DynamoDB, CloudWatch
- Communication: MQTT over TLS, WebSocket
- Security: X.509 certificates, AWS IAM policies

## Installation

### Prerequisites
- Python 3.8 or higher
- AWS Account with IoT Core access
- Git

### Quick Start

1. Clone the repository
   ```bash
   git clone https://github.com/EnasJa/HVAC_PROJECT.git
   cd hvac-iot-monitoring-system
   ```

2. Create virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up AWS certificates (see Configuration section)

5. Run the application
   ```bash
   python app.py
   ```

6. Access the dashboard at http://localhost:5000

## Configuration

### AWS IoT Core Setup

1. Create IoT Thing in AWS Console
   - Go to AWS IoT Core -> Manage -> Things
   - Create a new thing named `hvac-building-sensor`
   - Download certificates and keys

2. Certificate Setup
   ```bash
   mkdir certificates
   # Copy your downloaded certificates to certificates/ folder:
   # - device-certificate.pem.crt
   # - private-key.pem.key
   # - AmazonRootCA1.pem
   ```

3. Update Configuration
   ```python
   # aws_config.py
   AWS_IOT_ENDPOINT = "your-endpoint.iot.region.amazonaws.com"
   DEVICE_CERT = "certificates/device-certificate.pem.crt"
   PRIVATE_KEY = "certificates/private-key.pem.key"
   ROOT_CA = "certificates/AmazonRootCA1.pem"
   ```

## Usage

### Starting the System

1. Run the sensor simulator:
   ```bash
   python hvac_aws_simulator.py
   ```

2. Start the dashboard server:
   ```bash
   python app.py
   ```

3. Monitor the system:
   - Open http://localhost:5000
   - View real-time environmental data
   - Monitor alerts and system status

### API Endpoints

```
GET /api/data          # Returns all current sensor data and statistics
GET /api/zones         # Returns list of monitored zones
GET /api/history/{zone} # Returns historical data for specific zone
GET /                  # Main dashboard interface
```

## Project Structure

```
hvac-iot-monitoring-system/
├── app.py                 # Main Flask application
├── hvac_aws_simulator.py  # IoT sensor simulator
├── aws_config.py          # AWS configuration
├── templates/
│   └── dashboard.html     # Web dashboard interface
├── certificates/          # AWS IoT certificates (ignored by git)
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## Performance

- Processing Latency: < 2 seconds (sensor to dashboard)
- Message Throughput: 120+ daily executions
- Uptime: 99.8% availability
- Concurrent Zones: 10+ zones tested successfully
- Alert Response: < 5 seconds detection to notification

## Academic Context

This project was developed as part of the Internet of Things (IoT) course at SCE - Shamoon College of Engineering under the guidance of Guy Tel Zur.

**Research Contributions:**
- Practical implementation of IoT technologies in building automation
- Demonstration of cloud-native architecture for IoT applications
- Real-time data processing and visualization techniques
- Integration of multiple AWS services for comprehensive IoT solutions


## Security Note

Never commit AWS certificates or keys to the repository. The .gitignore file is configured to protect sensitive files.