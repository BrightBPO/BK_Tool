import requests
from flask import Blueprint, jsonify, request
from peewee import Model, CharField, DateTimeField, AutoField
from db_config import db
from datetime import datetime

pacer_blueprint = Blueprint('pacer', __name__, url_prefix='/pacer')
class BaseModel(Model):
    """
    Base model that defines the database for all models.
    """
    class Meta:
        database = db

class PacerCredentials(BaseModel):
    pacer_id = AutoField()
    prod_username = CharField(null=True)
    prod_password = CharField(null=True)
    qa_username = CharField(null=True)
    qa_password = CharField(null=True)
    mode = CharField(choices=[("qa", "QA"), ("prod", "Production")], default="qa")
    created_at = DateTimeField(default=lambda: datetime.now())
    
    class Meta:
        table_name = 'PacerCredentials'
        

with db.connection_context():
        db.create_tables([PacerCredentials])


@pacer_blueprint.route('/update-credentials', methods=['POST']) 
def update_pacer_credentials():
    try:
        data = request.json
        mode = data.get("mode") # qa or production
        username = data.get("username")
        password = data.get("password")

        if not any([mode, username, password]): # Ensure at least one field is provided
            return jsonify({"error": "Provide at least one field to update"}), 400
        
        with db.atomic():
            pacer = get_pacer_()

            if mode == "production":
                pacer_credentials_dict = {
                    "mode": mode,
                    "prod_username": username,
                    "prod_password": password,
                }
            else:
                pacer_credentials_dict = {
                    "mode": mode,
                    "qa_username": username,
                    "qa_password": password
                }

            if pacer: # credentials exists than update them 
                PacerCredentials.update(pacer_credentials_dict).where(
                    PacerCredentials.pacer_id==pacer["pacer_id"]
                ).execute()
            else: # create credentials
                PacerCredentials.create(**pacer_credentials_dict)
            

        return jsonify({"message": "PACER credentials updated successfully!"})

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    
@pacer_blueprint.route('/get', methods=['GET'])
def get_pacer_credentials():
    
    pacer = get_pacer_()
    if pacer:
        return jsonify(pacer)
    return jsonify({"error": "No PACER credentials found"}), 404

def get_pacer_():
    pacer = PacerCredentials.select().order_by(PacerCredentials.pacer_id.desc()).first()
    if pacer:
        return {
            "pacer_id": pacer.pacer_id,
            "qa_username": pacer.qa_username,
            "qa_password": pacer.qa_password,
            "prod_username": pacer.prod_username,
            "prod_password": pacer.prod_password,
            "mode": pacer.mode
        }
    
    return None

# Authenticate with PACER API
def authenticate_pacer():
    try:
        pacer = get_pacer_()

        if not pacer:
            return None
        
        # PACER credentials
        pacer_username = pacer.get("username")
        pacer_password = pacer.get("password")

        auth_api_url = pacer.get("auth_api_url")

        payload = {
            "loginId": pacer_username, 
            "password": pacer_password, 
            "redactFlag": "1"
        }
        headers = {
            "Content-Type": "application/json", 
            "Accept": "application/json"
        }

        response = requests.post(
            auth_api_url, 
            json=payload, 
            headers=headers
        )

        response.raise_for_status()

        auth_data = response.json()
        
        if auth_data.get("loginResult") == "0":
            return auth_data.get("nextGenCSO")
        else:
            print(f"Authentication failed: {auth_data.get('errorDescription')}")
            return None
        
    except requests.RequestException as e:
        print(f"Error authenticating with PACER: {e}")
        return None

#Search case by case number
def search_case(case_number):
    """
    Searches for a case by its number using the PACER API.
    """
    if not case_number:
        raise ValueError("caseNumberFull is required.")

    token = authenticate_pacer()
    if not token:
        raise ValueError("PACER authentication failed.")

    pacer = get_pacer_()

    # API details
    search_api_url = pacer.get("search_api_url")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-NEXT-GEN-CSO": token
    }

    payload = {"caseNumberFull": case_number}

    try:
        response = requests.post(search_api_url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200:
            content = response_data.get("content", [])
            if not content:
                return None  # No case found
            return content[0]  # Return the first matching case
        
        # Handle specific errors from PACER
        error_details = response_data.get("error", [])
        error_message = "; ".join([f"{err.get('field')}: {', '.join(err.get('messages', []))}" for err in error_details])
        raise ValueError(f"PACER API Error - {error_message or response.text}")

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to connect to PACER API: {str(e)}")


#resp = search_case("0:2017bk05806")
#print(resp)

case_numbers = ["0:2015bk01946", "T:2016bk02360", "0:2015bk01946", "0:2017bk05669", "5:2012bk99999", 
                "0:2017bk05806", "0:2017bk05810", "0:2017bk05811", "0:2017bk05812", "0:2017bk05813", 
                "0:2017bk05819", "1:2001bk00069", "1:2001bk00080", "6:2015bk00066", "1:2001bk00069", 
                "1:2001bk00080", "6:2015bk00066", "4:2019bk00019", "1:2001bk00069", "1:2001bk00080", 
                "0:2013mp00014", "6:2016bk00044", "6:2016ap00017", "6:2016ap00018", "0:2013mp00014", 
                "6:2016bk00044", "6:2016ap00017", "6:2016ap00018", "0:2010bk01973", "1:2014mp00101", 
                "0:2010bk01973", "1:2014mp00101", "0:2009bk01076", "5:2009bk01318", "5:2009bk01319", 
                "5:2009bk01324", "1:2009bk01532", "1:2009bk01532", "1:2009ap01537", "1:2009bk01548", 
                "5:2009bk01659", "1:2009mp01684", "1:2009ap01713", "1:2010ap01028", "1:2010bk01077", 
                "0:2010bk11111", "0:2010bk09999", "1:2010ap01362", "0:2010bk01973", "4:2010ap02044", 
                "0:2010bk02059", "0:2010bk02361", "1:2011bk01015"]