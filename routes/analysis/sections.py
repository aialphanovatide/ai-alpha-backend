from http import HTTPStatus
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from config import Sections, Session
from typing import Dict, Any, Tuple

sections_bp = Blueprint('sections_bp', __name__)

@sections_bp.route('/sections', methods=['GET'])
def get_all_sections():
    """
    Retrieve all sections.
    
    Returns:
        dict: A JSON response containing the list of sections.
        Format: {"message": list, "error": str or None, "status": int}
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK
    }
    with Session() as session:
        try:
            sections = session.query(Sections).all()
            sections_list = [section.as_dict() for section in sections]
            response["message"] = sections_list
        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error: {str(e)}"
            response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            session.close()
        
        return jsonify(response), response["status"]

VALID_TARGETS = {'article', 'narrative_trading', 'analysis', 's_and_r_analysis'}

def validate_section_data(data: Dict[str, Any]):
    """
    Validate the section data from the request.
    
    Args:
        data: Dictionary containing section data
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not data or not isinstance(data, dict):
        return False, "Data must be a dictionary"
     
    # Check for required fields
    required_fields = {'name', 'description', 'target'}
    missing_fields = required_fields - set(data.keys())
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate field types and constraints
    if not isinstance(data['name'], str) or not data['name'].strip():
        return False, "Name must be a non-empty string"
    
    if not isinstance(data['description'], str) or not data['description'].strip():
        return False, "Description must be a non-empty string"
    
    if not isinstance(data['target'], str) or data['target'] not in VALID_TARGETS:
        return False, f"Target must be one of: {', '.join(VALID_TARGETS)}"
    
    return True, ""

@sections_bp.route('/sections', methods=['POST'])
def create_section():
    """
    Create a new section.
    
    Request Body:
        dict: The section data to be created.
        Keys: 
            - name (str): The name of the section
            - description (str): A description of the section's purpose
            - target (str): The target type (article, narrative_trading, analysis, s_and_r_analysis)
    
    Returns:
        Tuple[dict, int]: A JSON response containing the created section and HTTP status code.
        Response Format: {
            "message": dict or None,
            "error": str or None,
            "status": int
        }
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.CREATED
    }
    
    try:
        # Get and validate request data
        section_data = request.get_json()
        if not section_data:
            response.update({
                "error": "No data provided",
                "status": HTTPStatus.BAD_REQUEST
            })
            return jsonify(response), response["status"]
        
        # Validate section data
        is_valid, error_message = validate_section_data(section_data)
        if not is_valid:
            response.update({
                "error": error_message,
                "status": HTTPStatus.BAD_REQUEST
            })
            return jsonify(response), response["status"]
        
        # Clean input data
        cleaned_data = {
            'name': section_data['name'].strip(),
            'description': section_data['description'].strip(),
            'target': section_data['target'].lower()
        }
        
        with Session() as session:
            # Check if section with same name already exists
            existing_section = session.query(Sections).filter(
                Sections.name == cleaned_data['name']
            ).first()
            
            if existing_section:
                response.update({
                    "error": f"Section with name '{cleaned_data['name']}' already exists",
                    "status": HTTPStatus.CONFLICT
                })
                return jsonify(response), response["status"]
            
            # Create new section
            new_section = Sections(**cleaned_data)
            session.add(new_section)
            session.commit()
            session.refresh(new_section)
            
            response["message"] = new_section.as_dict()
            
    except SQLAlchemyError as e:
        response.update({
            "error": f"Database error: {str(e)}",
            "status": HTTPStatus.INTERNAL_SERVER_ERROR
        })
    except Exception as e:
        response.update({
            "error": f"An unexpected error occurred: {str(e)}",
            "status": HTTPStatus.INTERNAL_SERVER_ERROR
        })
    
    return jsonify(response), response["status"]

@sections_bp.route('/sections/<int:section_id>', methods=['DELETE'])
def delete_section(section_id):
    """
    Delete a section by its ID.
    
    Parameters:
        section_id (int): The ID of the section to be deleted.
    
    Returns:
        dict: A JSON response indicating the success or failure of the operation.
        Format: {"message": str, "error": str or None, "status": int}
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK
    }
    with Session() as session:
        try:
            section = session.query(Sections).get(section_id)
            
            if not section:
                response["error"] = "Section not found"
                response["status"] = HTTPStatus.NOT_FOUND
                return jsonify(response), response["status"]
            
            session.delete(section)
            session.commit()
            response["message"] = f"Section with ID {section_id} has been deleted"
        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error: {str(e)}"
            response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            session.close()
        
        return jsonify(response), response["status"]