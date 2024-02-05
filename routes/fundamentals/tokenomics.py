from flask import Blueprint, request, jsonify
from config import Token_distribution, Token_utility, Value_accrual_mechanisms, session
from sqlalchemy.orm import joinedload

tokenomics = Blueprint('tokenomics', __name__)

# ------- GET ------------ GETS THREE TOKENOMICS, Token_distribution, Token_utility AND Value_accrual_mechanisms ------------------------

@tokenomics.route('/get_tokenomics/<int:coin_bot_id>', methods=['GET'])
def get_tokenomics(coin_bot_id):
    try:
        token_distribution_obj = session.query(Token_distribution).filter(Token_distribution.coin_bot_id == coin_bot_id).all()
        token_utility_obj = session.query(Token_utility).filter(Token_utility.coin_bot_id == coin_bot_id).all()
        value_accrual_mechanisms_obj = session.query(Value_accrual_mechanisms).filter(Value_accrual_mechanisms.coin_bot_id == coin_bot_id).all()

        token_distribution_data = [{
            'token_distributions': token_distribution.as_dict(),
        } for token_distribution in token_distribution_obj]

        token_utility_data = [{
            'token_utilities': token_utility.as_dict(),
        } for token_utility in token_utility_obj]

        value_accrual_mechanisms_data = [{
            'value_accrual_mechanisms': value_accrual_mechanisms.as_dict(),
        } for value_accrual_mechanisms in value_accrual_mechanisms_obj]

        final_obj = {
            'token_distribution': token_distribution_data,
            'token_utility': token_utility_data,
            'value_accrual_mechanisms': value_accrual_mechanisms_data,
        }
        
        return jsonify({'message': final_obj}), 200
         
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# ------- POST ---------- CREATES A NEW INSTANCE OF THE TABLE ----------------------------------

@tokenomics.route('/post_token_utility', methods=['POST'])
def create_token_utility():

    try:
        data = request.get_json()
        coin_bot_id = data['coin_bot_id']
        token_application = data['token_application']
        description = data['description']

        if coin_bot_id is None or (coin_bot_id is not None and not isinstance(coin_bot_id, int)):
            return jsonify({'message': 'Coin ID is required', 'status': 400}), 400
        
        new_token_utility = Token_utility(
            token_application=token_application,
            description=description,
            coin_bot_id=coin_bot_id
        )
        session.add(new_token_utility)
        session.commit()
        return jsonify({'message': 'Token utility added successfully', 'status': 200}), 200
       
    except Exception as e:
        return jsonify({'error': f'Error creating a Token utility: {str(e)}', 'status': 500}), 500


@tokenomics.route('/post_token_distribution', methods=['POST'])
def create_token_distribution():

    try:
        data = request.get_json()
        coin_bot_id = data['coin_bot_id']
        holder_category = data['holder_category']
        percentage_held = data['percentage_held']

        if coin_bot_id is None or (coin_bot_id is not None and not isinstance(coin_bot_id, int)):
            return jsonify({'message': 'Coin ID is required', 'status': 400}), 400
        
        new_token_distribution = Token_distribution(
            holder_category=holder_category,
            percentage_held=percentage_held,
            coin_bot_id=coin_bot_id
        )
        session.add(new_token_distribution)
        session.commit()
        return jsonify({'message': 'Token distribution added successfully', 'status': 200}), 200
       
    except Exception as e:
        return jsonify({'error': f'Error creating a token distribution: {str(e)}', 'status': 500}), 500


@tokenomics.route('/post_value_accrual_mechanisms', methods=['POST'])
def create_value_accrual_mechanisms():

    try:
        data = request.get_json()
        coin_bot_id = data['coin_bot_id']
        mechanism = data['mechanism']
        description = data['description']

        if coin_bot_id is None or (coin_bot_id is not None and not isinstance(coin_bot_id, int)):
            return jsonify({'message': 'Coin ID is required', 'status': 400}), 400
        
        new_value_accrual_mechanisms = Token_distribution(
            mechanism=mechanism,
            description=description,
            coin_bot_id=coin_bot_id
        )
        session.add(new_value_accrual_mechanisms)
        session.commit()
        return jsonify({'message': 'Value accrual mechanisms added successfully', 'status': 200}), 200
       
    except Exception as e:
        return jsonify({'error': f'Error creating a value accrual mechanisms: {str(e)}', 'status': 500}), 500


# ------- PUT ---------- EDITS AN INSTANCE OF THE TABLE ----------------------------------------
    

@tokenomics.route('/edit_tokenomics/<int:tokenomics_id>', methods=['PUT'])  
def edit_competitor_data(tokenomics_id):
    try: 
        data = request.json
        token_distribution_data = session.query(Token_distribution).filter(Token_distribution.id == tokenomics_id).first()
        token_utility_data = session.query(Token_utility).filter(Token_utility.id == tokenomics_id).first()
        Value_accrual_mechanisms_data = session.query(Value_accrual_mechanisms).filter(Value_accrual_mechanisms.id == tokenomics_id).first()

        if not data['token_distribution'] or not data['token_utility'] or not data['value_accrual_mechanisms']:
            return jsonify({'message': f'Tokenomics data required', 'status': 400}), 400

        if token_distribution_data and data['token_distribution'].items():
            for key, value in data['token_distribution'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(token_distribution_data, key, value)
        
        if token_utility_data and data['token_utility'].items():
            for key, value in data['token_utility'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(token_utility_data, key, value)
        
        if Value_accrual_mechanisms_data and data['value_accrual_mechanisms'].items():
            for key, value in data['value_accrual_mechanisms'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(Value_accrual_mechanisms_data, key, value)

        session.commit()
        return jsonify({'message': f'Tokenomics edited successfully', 'status': 200}), 200
    
    except Exception as e:
        return jsonify({'error': f'Error editing Tokenomics data: {str(e)}', 'status': 500}), 500
   
