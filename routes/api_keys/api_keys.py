# Endpoints to create and Delete API KEYS

from flask import Blueprint, request, jsonify
from config import Session, APIKey, Admin
from sqlalchemy.exc import SQLAlchemyError

api_keys_bp = Blueprint('api_keys_bp', __name__)


@api_keys_bp.route('/api-keys/<int:admin_id>', methods=['POST'])
def create_or_regenerate_api_key(admin_id):
    """
    Create a new API key or regenerate an existing one for the given admin ID.
    """
    session = Session()
    try:
        # Check if the admin exists
        admin = session.query(Admin).filter_by(admin_id=admin_id).first()
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404

        # Check if the admin already has an API key
        existing_api_key = session.query(APIKey).filter_by(admin_id=admin_id).first()

        if existing_api_key:
            # Regenerate the API key
            new_key = APIKey.generate_api_key()
            existing_api_key.key = new_key
            existing_api_key.last_used = None  # Reset last_used
            session.commit()
            message = 'API key regenerated successfully'
            api_key_data = existing_api_key.as_dict()
        else:
            # Create a new API key
            new_api_key = APIKey.create_new_key(admin_id)
            message = 'API key created successfully'
            api_key_data = new_api_key

        return jsonify({'message': message, 'data': api_key_data}), 200

    except ValueError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500
    finally:
        session.close()

@api_keys_bp.route('/api-keys/<int:admin_id>', methods=['DELETE'])
def delete_api_key(admin_id):
    """
    Delete the API key for the given admin ID.
    """
    session = Session()
    try:
        api_key = session.query(APIKey).filter_by(admin_id=admin_id).first()
        if not api_key:
            return jsonify({'error': 'No API key found for this admin'}), 404
        
        session.delete(api_key)
        session.commit()
        return jsonify({'message': 'API key deleted successfully'}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500
    finally:
        session.close()



