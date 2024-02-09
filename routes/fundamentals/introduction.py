from flask import Blueprint, request, jsonify
from config import Introduction, session, CoinBot
from datetime import datetime

introduction = Blueprint('introduction', __name__)


# creates an introduction for a coin - allow just once
@introduction.route('/post_introduction', methods=['POST'])
def create_content():
    try:
        data = request.get_json()

        coin_bot_id = data.get('coin_bot_id')
        content = data.get('content')
        website = data.get('website', None)
        whitepaper = data.get('whitepaper', None)

        existing_introduction = session.query(Introduction).filter_by(coin_bot_id=int(coin_bot_id)).first()

        if existing_introduction:
            return jsonify({'message': 'A record already exists for this Coin', 'status': 400}), 400

        new_introduction = Introduction(coin_bot_id=coin_bot_id, 
                                        content=content,
                                        website=website,
                                        whitepaper=whitepaper
                                        )
        session.add(new_introduction)
        session.commit()
        return jsonify({'message': 'Content created successfully', 'status': 200}), 200
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500
    


# Gets the introduction data of a coin
@introduction.route('/get_introduction/<string:coin_name>', methods=['GET'])
def get_content(coin_name):
    try:
        coin_data = session.query(CoinBot).filter(CoinBot.bot_name==coin_name).first()

        if coin_data == None:
            return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404
        
        introduction = session.query(Introduction).filter_by(coin_bot_id=coin_data.bot_id).first()

        if introduction:
            introduction_data = introduction.as_dict()
            return jsonify({'message': introduction_data, 'status': 200}), 200
        else:
            return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404

    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500
    


# Edits the introduction of a coin by passing the ID of it and the values to modify by Body
@introduction.route('/edit_introduction/<int:coin_bot_id>', methods=['PUT'])
def edit_content(coin_bot_id):
    try:
        data = request.get_json()

        existing_introduction = session.query(Introduction).filter_by(coin_bot_id=coin_bot_id).first()

        if existing_introduction:
            # Update content if key 'content' exists in the payload and its value is not empty
            if 'content' in data and data['content'] != '':
                existing_introduction.content = data['content']

            # Update website if key 'website' exists in the payload and its value is not empty
            if 'website' in data and data['website'] != '':
                existing_introduction.website = data['website']

            # Update whitepaper if key 'whitepaper' exists in the payload and its value is not empty
            if 'whitepaper' in data and data['whitepaper'] != '':
                existing_introduction.whitepaper = data['whitepaper']

            existing_introduction.updated_at = datetime.utcnow()
            session.commit()

            return jsonify({'message': 'Content updated successfully', 'status': 200}), 200
        else:
            return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404

    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


  

