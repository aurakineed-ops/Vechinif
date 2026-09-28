import requests
import json
from datetime import datetime
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DEVELOPER = "@sahilxalone"
VERSION = "1.0.0"
APP_NAME = "Vehicle Insurance API"
DESCRIPTION = "API for fetching vehicle insurance information from RiskCovry"

class VehicleInsuranceAPI:
    
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', "https://api.riskcovry.com")
        self.headers = {
            "host": "api.riskcovry.com",
            "user-agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36",
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://sureraksha.ttibi.co.in",
            "referer": "https://sureraksha.ttibi.co.in/"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session_token = None
        self.token_expiry = None
    
    def get_session_token(self, category_id=340):
        url = f"{self.base_url}/quotation_searches.json"
        payload = {
            "category_id": category_id,
            "device_type": "Desktop"
        }
        
        try:
            logger.info(f"Requesting session token for category: {category_id}")
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.session_token = data.get("session_token")
            
            if self.session_token:
                logger.info("Session token extracted successfully")
                return self.session_token
            else:
                logger.error("Failed to extract session token from response")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout while getting session token")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting session token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def get_vehicle_info(self, registration_number, session_token=None):
        if not registration_number:
            return {"error": "Registration number is required"}, 400
        
        token = session_token or self.session_token
        if not token:
            token = self.get_session_token()
            if not token:
                return {"error": "Failed to get session token"}, 500
        
        url = f"{self.base_url}/vehicles/fetch_vehicle_info"
        params = {
            "registration_number": registration_number.upper().strip(),
            "quote_id": token
        }
        
        try:
            logger.info(f"Fetching vehicle info for: {registration_number}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json(), 200
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout while fetching vehicle info")
            return {"error": "Request timeout"}, 504
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching vehicle info: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e)}, 500
    
    def format_vehicle_response(self, vehicle_data):
        if not vehicle_data:
            return {}
        
        def format_address(address_data):
            if address_data:
                return f"{address_data.get('address', '')} - {address_data.get('pincode', '')}"
            return "N/A"
        
        return {
            "registration_details": {
                "registration_number": vehicle_data.get('registration_number', 'N/A'),
                "registration_date": vehicle_data.get('registration_date', 'N/A'),
                "registration_authority": vehicle_data.get('registered_at', 'N/A'),
                "rto_code": vehicle_data.get('rto_code', 'N/A'),
                "registration_status": vehicle_data.get('rc_status', 'N/A'),
                "rc_valid_until": vehicle_data.get('rc_fit_upto', 'N/A')
            },
            "vehicle_specifications": {
                "make": vehicle_data.get('make', 'N/A'),
                "model": vehicle_data.get('model', 'N/A'),
                "variant": vehicle_data.get('variant', 'N/A'),
                "vehicle_type": vehicle_data.get('vehicle_type', 'N/A'),
                "class_category": vehicle_data.get('class_category', 'N/A'),
                "fuel_type": vehicle_data.get('fuel_descritpion', 'N/A'),
                "cubic_capacity": vehicle_data.get('cubic_capacity', 'N/A'),
                "seat_capacity": vehicle_data.get('seat_capacity', 'N/A'),
                "manufacturing_month_year": vehicle_data.get('manufactoring_month_year', 'N/A')
            },
            "vehicle_identification": {
                "chassis_number": vehicle_data.get('chassis_number', 'N/A'),
                "engine_number": vehicle_data.get('engine_number', 'N/A')
            },
            "address_information": {
                "permanent_address": format_address(vehicle_data.get('permanent_address_split')),
                "correspondence_address": format_address(vehicle_data.get('correspondence_address_split'))
            },
            "insurance_details": {
                "previous_insurance_carrier": vehicle_data.get('previous_insurance_carrier', 'N/A'),
                "previous_policy_number": vehicle_data.get('previous_policy_number', 'N/A'),
                "previous_policy_valid_until": vehicle_data.get('previous_policy_valid_upto', 'N/A')
            },
            "additional_information": {
                "financer": vehicle_data.get('financer', 'N/A'),
                "owner_count": vehicle_data.get('owner_count', 'N/A'),
                "blacklist_status": vehicle_data.get('black_list_status', 'N/A'),
                "pucc_number": vehicle_data.get('pucc_number', 'N/A'),
                "pucc_expiry_date": vehicle_data.get('pucc_expiry_date', 'N/A')
            },
            "internal_codes": {
                "make_code": vehicle_data.get('internal_make_code', 'N/A'),
                "model_code": vehicle_data.get('internal_model_code', 'N/A'),
                "variant_code": vehicle_data.get('internal_variant_code', 'N/A')
            }
        }

api_client = VehicleInsuranceAPI()

@app.route('/', methods=['GET'])
def home():
    response = {
        "service": APP_NAME,
        "version": VERSION,
        "developer": DEVELOPER,
        "description": DESCRIPTION,
        "endpoints": {
            "/health": "GET - Health check",
            "/api/session": "POST - Get session token",
            "/api/vehicle/<registration_number>": "GET - Get vehicle info",
            "/api/vehicle/details": "POST - Get vehicle info with formatting",
            "/api/vehicle/search": "POST - Search vehicle with custom options"
        },
        "port": 5029
    }
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": APP_NAME,
        "developer": DEVELOPER,
        "version": VERSION
    }
    return jsonify(response)

@app.route('/api/session', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    category_id = data.get('category_id', 340)
    token = api_client.get_session_token(category_id)
    
    if token:
        response = {
            "success": True,
            "session_token": token,
            "developer": DEVELOPER,
            "message": "Session created successfully"
        }
        return jsonify(response)
    else:
        response = {
            "success": False,
            "error": "Failed to create session",
            "developer": DEVELOPER
        }
        return jsonify(response), 500

@app.route('/api/vehicle/<registration_number>', methods=['GET'])
def get_vehicle_info(registration_number):
    session_token = request.args.get('session_token')
    data, status_code = api_client.get_vehicle_info(registration_number, session_token)
    
    if status_code == 200:
        response = {
            "success": True,
            "developer": DEVELOPER,
            "data": data
        }
        return jsonify(response)
    else:
        response = {
            "success": False,
            "error": data.get('error', 'Unknown error'),
            "developer": DEVELOPER
        }
        return jsonify(response), status_code

@app.route('/api/vehicle/details', methods=['POST'])
def get_vehicle_details():
    data = request.get_json()
    
    if not data or 'registration_number' not in data:
        response = {
            "success": False,
            "error": "Registration number is required",
            "developer": DEVELOPER
        }
        return jsonify(response), 400
    
    registration_number = data['registration_number']
    session_token = data.get('session_token')
    vehicle_data, status_code = api_client.get_vehicle_info(registration_number, session_token)
    
    if status_code == 200:
        formatted_data = api_client.format_vehicle_response(vehicle_data)
        response = {
            "success": True,
            "developer": DEVELOPER,
            "data": formatted_data,
            "raw_data": vehicle_data
        }
        return jsonify(response)
    else:
        response = {
            "success": False,
            "error": vehicle_data.get('error', 'Unknown error'),
            "developer": DEVELOPER
        }
        return jsonify(response), status_code

@app.route('/api/vehicle/search', methods=['POST'])
def search_vehicle():
    data = request.get_json()
    
    if not data or 'registration_number' not in data:
        response = {
            "success": False,
            "error": "Registration number is required",
            "developer": DEVELOPER
        }
        return jsonify(response), 400
    
    registration_number = data['registration_number']
    session_token = data.get('session_token')
    include_raw = data.get('include_raw', False)
    vehicle_data, status_code = api_client.get_vehicle_info(registration_number, session_token)
    
    if status_code == 200:
        response = {
            "success": True,
            "developer": DEVELOPER,
            "data": api_client.format_vehicle_response(vehicle_data),
            "timestamp": datetime.now().isoformat()
        }
        if include_raw:
            response["raw_data"] = vehicle_data
        return jsonify(response)
    else:
        response = {
            "success": False,
            "error": vehicle_data.get('error', 'Unknown error'),
            "developer": DEVELOPER
        }
        return jsonify(response), status_code

@app.errorhandler(404)
def not_found(error):
    response = {
        "success": False,
        "error": "Endpoint not found",
        "developer": DEVELOPER
    }
    return jsonify(response), 404

@app.errorhandler(500)
def internal_error(error):
    response = {
        "success": False,
        "error": "Internal server error",
        "developer": DEVELOPER
    }
    return jsonify(response), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5029, debug=True)
