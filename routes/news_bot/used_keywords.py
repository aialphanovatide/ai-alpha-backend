from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from config import Used_keywords, session

# Create a Blueprint for the scraping module routes
news_bots_features_bp = Blueprint(
    'news_bots_features_bp', __name__,
    template_folder='templates',
    static_folder='static'
)



@news_bots_features_bp.route('/api/get_used_keywords_to_download', methods=['GET'])
def get_used_keywords_to_download():
    try:
        coin_bot_id = request.args.get('coin_bot_id', type=int)
        time_period = request.args.get('time_period', default='3d')

        end_date = datetime.now()
        if time_period == "1w":
            start_date = end_date - timedelta(weeks=1)
        elif time_period == "1m":
            start_date = end_date - timedelta(days=30)
        elif time_period == "3m":
            start_date = end_date - timedelta(days=90)
        else:
            return jsonify({"error": "Invalid time period provided"}), 400

        used_keywords_query = session.query(Used_keywords.keywords).filter(
            Used_keywords.coin_bot_id == coin_bot_id,
            Used_keywords.created_at >= start_date,
            Used_keywords.created_at <= end_date
        ).all()

        # Unify all keywords into a single string
        all_keywords = ' '.join([kw.keywords for kw in used_keywords_query])

        # Split the string into a list of unique keywords
        unique_keywords = list(set(all_keywords.split(', ')))

        # Optional: Sort the keywords alphabetically if desired
        unique_keywords.sort()

        return jsonify({"keywords": unique_keywords}), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500



# Define the GET route to fetch all used keywords
@news_bots_features_bp.route('/api/get/used_keywords', methods=['GET'])
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

