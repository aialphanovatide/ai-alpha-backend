# from flask import Blueprint, request, jsonify
# from config import Introduction, Session, CoinBot
# from datetime import datetime
# from sqlalchemy.exc import SQLAlchemyError

# introduction = Blueprint('introduction', __name__)


# @introduction.route('/post_introduction', methods=['POST'])
# def create_content():
#     with Session() as session:
#         try:
#             data = request.get_json()
#             # Convert coin_bot_id to integer and validate it exists
#             try:
#                 coin_bot_id = int(data.get('coin_bot_id'))
#             except (TypeError, ValueError):
#                 return jsonify({
#                     'message': 'Invalid coin ID format - must be an integer', 
#                     'status': 400
#                 }), 400

#             # Validate required fields
#             content = data.get('content')
#             if not content:
#                 return jsonify({
#                     'message': 'Content is required',
#                     'status': 400
#                 }), 400

#             # Check if coin_bot exists
#             coin_bot = session.query(CoinBot).filter_by(bot_id=coin_bot_id).first()
#             if not coin_bot:
#                 return jsonify({
#                     'message': f'Coin ID {coin_bot_id} does not exist',
#                     'status': 404
#                 }), 404

#             # Check for existing introduction
#             existing_intro = session.query(Introduction).filter_by(coin_bot_id=coin_bot_id).first()
#             if existing_intro:
#                 return jsonify({
#                     'message': 'An introduction already exists for this coin',
#                     'status': 409
#                 }), 409

#             # Create new introduction
#             new_introduction = Introduction(
#                 coin_bot_id=coin_bot_id,
#                 content=content,
#                 website=data.get('website'),
#                 whitepaper=data.get('whitepaper'),
#                 dynamic=data.get('dynamic', False)
#             )
            
#             session.add(new_introduction)
#             session.commit()
            
#             return jsonify({
#                 'message': 'Introduction created successfully',
#                 'status': 201,
#                 'data': new_introduction.as_dict()
#             }), 201

#         except SQLAlchemyError as e:
#             session.rollback()
#             return jsonify({
#                 'message': f'Database error: {str(e)}',
#                 'status': 500
#             }), 500
#         except Exception as e:
#             session.rollback()
#             return jsonify({
#                 'message': f'Unexpected error: {str(e)}',
#                 'status': 500
#             }), 500
#         finally:
#             session.close()
    


# # Gets the introduction data of a coin by ID or name
# @introduction.route('/api/get_introduction', methods=['GET'])
# def get_content():
#     try:
#         coin_id = request.args.get('id')
#         coin_name = request.args.get('coin_name')

#         if not coin_id and not coin_name:
#             return jsonify({'message': 'ID or coin name is required', 'status': 400}), 400
        
#         coin_data = None

#         if coin_name:
#             coin = session.query(CoinBot).filter(CoinBot.name==coin_name).first()
#             coin_data = session.query(Introduction).filter_by(coin_bot_id=coin.bot_id).first() if coin else None

#         if coin_id:
#             coin = session.query(Introduction).filter_by(coin_bot_id=coin_id).first()
#             coin_data = coin if coin else None

#         if coin_data == None:
#             return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404
        
#         introduction_data = coin_data.as_dict()
#         return jsonify({'message': introduction_data, 'status': 200}), 200
       
#     except Exception as e:
#         session.rollback()
#         return jsonify({'error': str(e), 'status': 500}), 500
    


# # Edits the introduction of a coin by passing the ID of it and the values to modify by Body
# @introduction.route('/edit_introduction/<int:coin_bot_id>', methods=['PUT'])
# def edit_content(coin_bot_id):
#     try:
#         data = request.get_json()

#         existing_introduction = session.query(Introduction).filter_by(coin_bot_id=coin_bot_id).first()

#         if existing_introduction:
#             # Update content if key 'content' exists in the payload and its value is not empty
#             if 'content' in data and data['content'] != '':
#                 existing_introduction.content = data['content']

#             # Update website if key 'website' exists in the payload and its value is not empty
#             if 'website' in data and data['website'] != '':
#                 existing_introduction.website = data['website']

#             # Update whitepaper if key 'whitepaper' exists in the payload and its value is not empty
#             if 'whitepaper' in data and data['whitepaper'] != '':
#                 existing_introduction.whitepaper = data['whitepaper']

#             existing_introduction.updated_at = datetime.now()
#             session.commit()

#             return jsonify({'message': 'Introduction updated successfully', 'status': 200}), 200
#         else:
#             return jsonify({'message': 'No record found for the specified ID', 'status': 404}), 404

#     except Exception as e:
#         session.rollback()
#         return jsonify({'error': str(e), 'status': 500}), 500


  

from flask import Blueprint, request, jsonify
from config import Introduction, Session, CoinBot
from sqlalchemy.exc import SQLAlchemyError

introduction = Blueprint('introduction', __name__)

@introduction.route('/introduction', methods=['POST'])
def create_content():
    """Create a new introduction for a coin"""
    response = {'success': False, 'message': None, 'data': None}
    
    with Session() as session:
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['coin_id', 'content', 'website', 'whitepaper']
            for field in required_fields:
                if not data.get(field):
                    response['message'] = f'{field} is required'
                    return jsonify(response), 400

            try:
                coin_id = int(data['coin_id'])
            except (TypeError, ValueError):
                response['message'] = 'Invalid coin_id format - must be an integer'
                return jsonify(response), 400

            # Check if coin_bot exists
            coin_bot = session.query(CoinBot).filter_by(bot_id=coin_id).first()
            if not coin_bot:
                response['message'] = f'Coin ID {coin_id} does not exist'
                return jsonify(response), 404

            # Check for existing introduction
            existing_intro = session.query(Introduction).filter_by(coin_bot_id=coin_id).first()
            if existing_intro:
                response['message'] = 'An introduction already exists for this coin'
                return jsonify(response), 409

            # Create new introduction
            new_introduction = Introduction(
                coin_bot_id=coin_id,
                content=data['content'],
                website=data['website'],
                whitepaper=data['whitepaper'],
                dynamic=data.get('dynamic', False)
            )
            
            session.add(new_introduction)
            session.commit()
            
            response['success'] = True
            response['message'] = 'Introduction created successfully'
            response['data'] = new_introduction.as_dict()
            return jsonify(response), 201

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
        except Exception as e:
            session.rollback()
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500

@introduction.route('/introduction/<int:coin_id>', methods=['GET'])
def get_content(coin_id):
    """
    Get introduction by coin ID.
    
    Args:
        coin_id (int): The ID of the coin to retrieve the introduction for.
        
    Returns:
        Response: JSON response containing the introduction data or error message.
    """
    response = {'success': False, 'message': None, 'data': None}
    
    with Session() as session:
        try:
            # Query for introduction directly using coin_bot_id
            introduction = session.query(Introduction).filter_by(coin_bot_id=coin_id).first()
            
            if not introduction:
                response['message'] = 'No introduction found for the specified coin'
                return jsonify(response), 404

            response['success'] = True
            response['data'] = introduction.as_dict()
            return jsonify(response), 200

        except SQLAlchemyError as e:
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
        except Exception as e:
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500

@introduction.route('/introduction/<int:coin_id>', methods=['PUT'])
def edit_content(coin_id):
    """Update introduction for a specific coin"""
    response = {'success': False, 'message': None, 'data': None}
    
    with Session() as session:
        try:
            data = request.get_json()

            # Validate that at least one field is provided
            if not any(key in data for key in ['content', 'website', 'whitepaper']):
                response['message'] = 'At least one field (content, website, or whitepaper) is required'
                return jsonify(response), 400

            existing_introduction = session.query(Introduction).filter_by(coin_bot_id=coin_id).first()
            if not existing_introduction:
                response['message'] = 'No introduction found for the specified coin'
                return jsonify(response), 404

            # Update fields if provided
            for field in ['content', 'website', 'whitepaper']:
                if field in data and data[field]:
                    setattr(existing_introduction, field, data[field])

            session.commit()
            
            response['success'] = True
            response['message'] = 'Introduction updated successfully'
            response['data'] = existing_introduction.as_dict()
            return jsonify(response), 200

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
        except Exception as e:
            session.rollback()
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500