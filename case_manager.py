from flask import Blueprint, jsonify, request
from peewee import Model, CharField, DateField, DateTimeField, AutoField, Case as peewee_case
import requests
from db_config import db
from datetime import datetime
from pacer import search_case

case_blueprint = Blueprint('case', __name__, url_prefix='/cases')

class BaseModel(Model):
    """
    Base model that defines the database for all models.
    """
    class Meta:
        database = db

class Case(BaseModel):
    case_id = AutoField()
    case_number = CharField(max_length=50, unique=True)  # Case number, must be unique
    debtor_name = CharField(max_length=255)  # Name of the debtor
    court = CharField(max_length=255)  # Court name
    filing_date = DateField(null=True)  # Filing date of the case
    dismissed_date = DateField(null=True)  # Dismissed date of the case
    created_at = DateTimeField(null=False)  # created date of the case
    updated_at = DateTimeField(null=True)

    class Meta:
        table_name = 'Case'

with db.connection_context():
        db.drop_tables([Case])
        db.create_tables([Case])


@case_blueprint.route('/refresh_all_cases', methods=['GET'])
def refresh_all_cases():
    """
    API endpoint to update all cases in the database by fetching case numbers from /cases/get_all_cases.
    """
    try:
        # Fetch all cases from /cases/get_all_cases
        response = requests.get(f"{request.host_url}cases/get_all_cases")
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch cases from /cases/get_all_cases"}), 500

        cases_data = response.json()
        cases_data = cases_data.get("cases")
        
        if not cases_data:
            return jsonify({"message": "No case found."}), 404

        # Fetch updated case details from PACER for all cases
        case_updates = {}
        for case in cases_data:
            case_number = case.get("case_number")
            case_number = case_number.strip()
            pacer_case_data = search_case(case_number)
            if pacer_case_data:
                case_updates[case_number] = {
                    "debtor_name": pacer_case_data.get("caseTitle"),
                    "court": pacer_case_data.get("courtId"),
                    "filing_date": pacer_case_data.get("dateFiled"),
                    "dismissed_date": pacer_case_data.get("dateDischarged", None),
                    "updated_at": datetime.now()
                }

        if not case_updates:
            return jsonify({"message": "No cases were updated."}), 404

        # Bulk update query using CASE statements
        query = Case.update(
            debtor_name=peewee_case(Case.case_number, [(cn, data["debtor_name"]) for cn, data in case_updates.items()]),
            court=peewee_case(Case.case_number, [(cn, data["court"]) for cn, data in case_updates.items()]),
            filing_date=peewee_case(Case.case_number, [(cn, data["filing_date"]) for cn, data in case_updates.items()]),
            dismissed_date=peewee_case(Case.case_number, [(cn, data["dismissed_date"]) for cn, data in case_updates.items()]),
            updated_at=peewee_case(Case.case_number, [(cn, data["updated_at"]) for cn, data in case_updates.items()])
        ).where(Case.case_number.in_(list(case_updates.keys())))
        
        rows_updated = query.execute()

        return jsonify({
            "message": f"{rows_updated} cases updated successfully!",
            "updated_cases": list(case_updates.keys())
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except ConnectionError as ce:
        return jsonify({"error": str(ce)}), 502
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@case_blueprint.route('/add_case', methods=['POST'])
def add_case():
    """
    API endpoint to add or update a case in the database.
    """
    try:
        case_data = request.get_json()
        case_number = case_data.get('case_number', '').strip()

        if not case_number:
            return jsonify({"error": "Case number is required."}), 400

        # Fetch case details
        pacer_case_data = search_case(case_number)

        if not pacer_case_data:
            return jsonify({"error": f"No details found for case {case_number}."}), 404

        # Map response data to your schema
        case_number_full = pacer_case_data.get("caseNumberFull")
        debtor_name = pacer_case_data.get("caseTitle")
        court = pacer_case_data.get("courtId")
        filing_date = pacer_case_data.get("dateFiled")
        dismissed_date = pacer_case_data.get("dateDischarged", None)

        with db.connection_context():
            case, created = Case.get_or_create(
                case_number=case_number_full,
                defaults={
                    'debtor_name': debtor_name,
                    'court': court,
                    'filing_date': filing_date,
                    'dismissed_date': dismissed_date,
                    'created_at': datetime.now()
                }
            )

            if not created:
                case.debtor_name = debtor_name
                case.court = court
                case.filing_date = filing_date
                case.dismissed_date = dismissed_date
                case.created_at = datetime.now()
                case.save()

        return jsonify({
            'message': 'Case added or updated successfully!',
            'case': {
                'case_id': case.case_id,
                'case_number': case.case_number,
                'debtor_name': case.debtor_name,
                'court': case.court,
                'filing_date': case.filing_date,
                'dismissed_date': case.dismissed_date,
                'created_at': case.created_at
            }
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except ConnectionError as ce:
        return jsonify({"error": str(ce)}), 502
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@case_blueprint.route('/get_all_cases', methods=['GET'])
def get_all_cases():
    """
    API endpoint to fetch all cases from the database.
    """
    try:
        with db.connection_context():
            # Query all cases
            cases = Case.select()

        # Convert cases to a list of dictionaries
        cases_data = [
            {
                'case_number': case.case_number,
                'debtor_name': case.debtor_name,
                'court': case.court,
                'filing_date': case.filing_date,
                'dismissed_date': case.dismissed_date,
                'created_at': case.created_at,
                'updated_at': case.updated_at,
            }
            for case in cases
        ]

        # Return the case data in JSON format
        return jsonify({
            'message': 'Cases retrieved successfully',
            'cases': cases_data
        }), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    

@case_blueprint.route('/delete_case', methods=['DELETE'])
def delete_case():
    """
    API endpoint to delete case from the database.
    """
    try:
        case_data = request.get_json()
        case_number = case_data.get('case_number', '').strip()

        with db.connection_context():
            rows_deleted = Case.delete().where(Case.case_number == case_number).execute()

        # Return the case data in JSON format
        return jsonify({
            'message': 'Case deleted successfully',
            'rows_deleted': rows_deleted
        }), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500