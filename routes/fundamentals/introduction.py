from flask import Blueprint, request, jsonify
from config import Introduction, session, CoinBot
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

introduction = Blueprint('introduction', __name__)


# creates an introduction for a coin - allow just once
@introduction.route('/post_introduction', methods=['POST'])
def create_content():
    try:
        data = request.get_json()
        
        # Convert coin_bot_id to integer and validate it exists
        try:
            coin_bot_id = int(data.get('coin_bot_id'))
        except (TypeError, ValueError):
            return jsonify({
                'message': 'Invalid coin_bot_id format - must be an integer', 
                'status': 400
            }), 400

        # Validate required fields
        content = data.get('content')
        if not content:
            return jsonify({
                'message': 'Content is required',
                'status': 400
            }), 400

        # Check if coin_bot exists
        coin_bot = session.query(CoinBot).filter_by(bot_id=coin_bot_id).first()
        if not coin_bot:
            return jsonify({
                'message': f'CoinBot with ID {coin_bot_id} does not exist',
                'status': 404
            }), 404

        # Check for existing introduction
        existing_intro = session.query(Introduction).filter_by(coin_bot_id=coin_bot_id).first()
        if existing_intro:
            return jsonify({
                'message': 'An introduction already exists for this CoinBot',
                'status': 409
            }), 409

        # Create new introduction
        new_introduction = Introduction(
            coin_bot_id=coin_bot_id,
            content=content,
            website=data.get('website'),
            whitepaper=data.get('whitepaper'),
            dynamic=data.get('dynamic', False)
        )
        
        session.add(new_introduction)
        session.commit()
        
        return jsonify({
            'message': 'Introduction created successfully',
            'status': 201,
            'data': new_introduction.as_dict()
        }), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({
            'message': f'Database error: {str(e)}',
            'status': 500
        }), 500
    except Exception as e:
        session.rollback()
        return jsonify({
            'message': f'Unexpected error: {str(e)}',
            'status': 500
        }), 500
    finally:
        session.close()
    


# Gets the introduction data of a coin by ID or name
@introduction.route('/api/get_introduction', methods=['GET'])
def get_content():
    try:
        coin_id = request.args.get('id')
        coin_name = request.args.get('coin_name')

        if not coin_id and not coin_name:
            return jsonify({'message': 'ID or coin name is required', 'status': 400}), 400
        
        coin_data = None

        if coin_name:
            coin = session.query(CoinBot).filter(CoinBot.name==coin_name).first()
            coin_data = session.query(Introduction).filter_by(coin_bot_id=coin.bot_id).first() if coin else None

        if coin_id:
            coin = session.query(Introduction).filter_by(coin_bot_id=coin_id).first()
            coin_data = coin if coin else None

        if coin_data == None:
            return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404
        
        introduction_data = coin_data.as_dict()
        return jsonify({'message': introduction_data, 'status': 200}), 200
       
    except Exception as e:
        session.rollback()
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

            return jsonify({'message': 'Introduction updated successfully', 'status': 200}), 200
        else:
            return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e), 'status': 500}), 500


  

