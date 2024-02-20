from flask import Blueprint, jsonify
from config import Used_keywords, session

# Create a Blueprint for the scraping module routes
scrapper_bp = Blueprint(
    'scrapper_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

# Define the GET route to fetch all used keywords
@scrapper_bp.route('/api/get/used_keywords', methods=['GET'])
def get_used_keywords():
    try:
        # Query all used keywords from the database
        used_keywords = session.query(Used_keywords).all()

        # If no used keywords found, return a 204 message with a JSON response
        if not used_keywords:
            return jsonify({'used_keywords': 'No used keywords found'}), 204
        else:
            # Convert Used_keywords objects to dictionaries and append them to a list
            used_keywords_list = [keyword.as_dict() for keyword in used_keywords]
            # Return the list of used keywords in JSON format with a 200 status code
            return jsonify({'used_keywords': used_keywords_list}), 200
           
    except Exception as e:
        # In case of error, return an error message with a 500 status code
        return jsonify({'error': f'An error occurred getting the used keywords: {str(e)}'}), 500
