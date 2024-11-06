from http import HTTPStatus
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from config import Sections, Session


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

@sections_bp.route('/sections', methods=['POST'])
def create_section():
    """
    Create a new section.
    
    Request Body:
        dict: The section data to be created.
        Keys: name, description, target
    
    Returns:
        dict: A JSON response containing the created section.
        Format: {"message": dict, "error": str or None, "status": int}
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.CREATED
    }
    with Session() as session:
        try:
            section_data = request.get_json()
            
            # Check if required fields are provided
            if 'name' not in section_data or 'description' not in section_data or 'target' not in section_data:
                response["error"] = "Missing required fields: name, description, target"
                response["status"] = HTTPStatus.BAD_REQUEST
                return jsonify(response), response["status"]
            
            new_section = Sections(
                name=section_data['name'],
                description=section_data['description'],
                target=section_data['target']
            )
            session.add(new_section)
            session.commit()
            response["message"] = new_section.as_dict()
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