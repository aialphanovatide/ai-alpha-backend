from flask import Blueprint, request, jsonify
from config import Token_distribution, Token_utility, Value_accrual_mechanisms, session, Tokenomics, CoinBot

tokenomics = Blueprint('tokenomics', __name__)

# ------- GET ------------ GETS THREE TOKENOMICS, Token_distribution, Token_utility AND Value_accrual_mechanisms ------------------------


@tokenomics.route('/api/get_tokenomics', methods=['GET'])
def get_tokenomics():
    try:
        coin_name = request.args.get('coin_name')
        coin_bot_id = request.args.get('coin_bot_id')

        if not coin_bot_id and not coin_name:
            return jsonify({'error': 'Coin ID or name is missing', 'status': 400}), 400

        coin_bot_id = coin_bot_id

        if coin_name:
            coin = session.query(CoinBot).filter(
                CoinBot.bot_name == coin_name).first()
            coin_bot_id = coin.bot_id if coin else None

        if coin_bot_id is None:
            return jsonify({'error': 'No tokenomics found for the requested coin', 'status': 404}), 404

        token_distribution_obj = session.query(Token_distribution).filter(
            Token_distribution.coin_bot_id == coin_bot_id).order_by(Token_distribution.created_at).all()
        token_utility_obj = session.query(Token_utility).filter(
            Token_utility.coin_bot_id == coin_bot_id).order_by(Token_utility.created_at).all()
        value_accrual_mechanisms_obj = session.query(Value_accrual_mechanisms).filter(
            Value_accrual_mechanisms.coin_bot_id == coin_bot_id).order_by(Value_accrual_mechanisms.created_at).all()
        tokenomics = session.query(Tokenomics).filter(
            Tokenomics.coin_bot_id == coin_bot_id).order_by(Tokenomics.created_at).all()

        token_distribution_data = [{
            'token_distributions': token_distribution.as_dict(),
        } for token_distribution in token_distribution_obj]

        tokenomics_data = [{
            'tokenomics': tokenomic.as_dict(),
        } for tokenomic in tokenomics]

        token_utility_data = [{
            'token_utilities': token_utility.as_dict(),
        } for token_utility in token_utility_obj]

        value_accrual_mechanisms_data = [{
            'value_accrual_mechanisms': value_accrual_mechanisms.as_dict(),
        } for value_accrual_mechanisms in value_accrual_mechanisms_obj]

        data = {
            'token_distribution': token_distribution_data,
            'token_utility': token_utility_data,
            'value_accrual_mechanisms': value_accrual_mechanisms_data,
            'tokenomics_data': tokenomics_data,
        }
        return jsonify({'message': data, 'status': 200}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500
    
#get tokenomic indivually
@tokenomics.route('/get_tokenomic/<int:id>', methods=['GET'])
def get_tokenomic(id):
    try:
        data = session.query(Tokenomics).filter(Tokenomics.id == id).first()

        if not data:
            return jsonify({'data': 'No tokenomic found', 'status': 404}), 404

        tokenomic_data = data.as_dict()
        return jsonify({'data': tokenomic_data, 'status': 200}), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500



# Get a token distribution
@tokenomics.route('/get_token_distribution/<int:id>', methods=['GET'])
def get_token_distribution(id):
    try:
        data = session.query(Token_distribution).filter(
            Token_distribution.id == id).first()

        if not data:
            return jsonify({'data': 'No token distribution found', 'status': 404}), 404
        if data:
            token_data = data.as_dict()
            return jsonify({'data': token_data, 'status': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500

# Get a token utility


@tokenomics.route('/get_token_utility/<int:id>', methods=['GET'])
def get_token_utility(id):
    try:
        data = session.query(Token_utility).filter(
            Token_utility.id == id).first()

        if not data:
            return jsonify({'data': 'No token utility found', 'status': 404}), 404
        if data:
            token_data = data.as_dict()
            return jsonify({'data': token_data, 'status': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500

# Get a value accrual mechanism


@tokenomics.route('/get_value_accrual/<int:id>', methods=['GET'])
def get_value_accrual(id):
    try:
        data = session.query(Value_accrual_mechanisms).filter(
            Value_accrual_mechanisms.id == id).first()

        if not data:
            return jsonify({'data': 'No value accrual found', 'status': 404}), 404
        if data:
            token_data = data.as_dict()
            return jsonify({'data': token_data, 'status': 200}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500

# ------- POST ---------- CREATES A NEW INSTANCE OF THE TABLE ----------------------------------


@tokenomics.route('/post_token_utility', methods=['POST'])
def create_token_utility():

    try:
        data = request.get_json()
        coin_bot_id = data.get('coin_bot_id')
        token_application = data.get('token_application')
        description = data.get('description')

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
        coin_bot_id = data.get('coin_bot_id')
        holder_category = data.get('holder_category')
        percentage_held = data.get('percentage_held')

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
        coin_bot_id = data.get('coin_bot_id')
        mechanism = data.get('mechanism')
        description = data.get('description')

        new_value_accrual_mechanisms = Value_accrual_mechanisms(
            mechanism=mechanism,
            description=description,
            coin_bot_id=coin_bot_id
        )
        session.add(new_value_accrual_mechanisms)
        session.commit()
        return jsonify({'message': 'Value accrual mechanisms added successfully', 'status': 200}), 200

    except Exception as e:
        return jsonify({'error': f'Error creating a value accrual mechanisms: {str(e)}', 'status': 500}), 500


@tokenomics.route('/post_tokenomics', methods=['POST'])
def create_tokenomics():
    try:
        data = request.get_json()
        coin_bot_id = data.get('coin_bot_id')
        token = data.get('token')
        total_supply = data.get('total_supply')
        circulating_supply = data.get('circulating_supply')
        percentage_circulating_supply = data.get(
            'percentage_circulating_supply')
        max_supply = data.get('max_supply')
        supply_model = data.get('supply_model')

        existance_tokenomics = session.query(Tokenomics).filter(
            Tokenomics.token == token.lower()).first()

        if existance_tokenomics:
            return jsonify({'error': 'Tokenomics already exist for this token', 'status': 409}), 409

        if not coin_bot_id:
            return jsonify({'error': 'Coin ID required', 'status': 400}), 400

        if token:
            new_tokenomics = Tokenomics(
                token=token,
                total_supply=total_supply,
                coin_bot_id=coin_bot_id,
                circulating_supply=circulating_supply,
                percentage_circulating_supply=percentage_circulating_supply,
                max_supply=max_supply,
                supply_model=supply_model
            )

            session.add(new_tokenomics)
            session.commit()
            return jsonify({'message': 'tokenomics added successfully', 'status': 200}), 200
        else:
            return jsonify({'error': f'Token name required', 'status': 400}), 400

    except Exception as e:
        return jsonify({'error': f'Error creating tokenomics mechanisms: {str(e)}', 'status': 500}), 500


# ------- PUT ---------- EDITS AN INSTANCE OF THE TABLE ----------------------------------------

# Create the edit route for editing a already created tokenomics

@tokenomics.route('/edit_tokenomics/<int:tokenomics_id>', methods=['PUT'])
def edit_competitor_data(tokenomics_id):
    try:
        data = request.json
        print("Data recibida:", data)

        token_distribution_data = session.query(Token_distribution).filter(
            Token_distribution.id == tokenomics_id).first()
        token_utility_data = session.query(Token_utility).filter(
            Token_utility.id == tokenomics_id).first()
        value_accrual_mechanisms_data = session.query(Value_accrual_mechanisms).filter(
            Value_accrual_mechanisms.id == tokenomics_id).first()
        tokenomics_data = session.query(Tokenomics).filter(
            Tokenomics.id == tokenomics_id).first()

        if not data['token_distribution'] or not data['token_utility'] or not data['value_accrual_mechanisms'] or not data['tokenomics']:
            return jsonify({'message': f'Tokenomics data required', 'status': 400}), 400

        if token_distribution_data and any(value != '' for value in data['token_distribution'].values()):
            print('In token distribution')
            for key, value in data['token_distribution'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(token_distribution_data, key, value)

        if token_utility_data and any(value != '' for value in data['token_utility'].values()):
            print('In token utility')
            for key, value in data['token_utility'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(token_utility_data, key, value)

        if value_accrual_mechanisms_data and any(value != '' for value in data['value_accrual_mechanisms'].values()):
            print('Value accrual')
            for key, value in data['value_accrual_mechanisms'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(value_accrual_mechanisms_data, key, value)

        if tokenomics_data and any(value != '' for value in data['tokenomics'].values()):
            print('In tokenomics')
            for key, value in data['tokenomics'].items():
                if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                    setattr(tokenomics_data, key, value)

        session.commit()
        return jsonify({'message': f'Data edited successfully', 'status': 200}), 200

    except Exception as e:
        return jsonify({'error': f'Error editing Tokenomics data: {str(e)}', 'status': 500}), 500



# ------- DELETE ---------- DELETE AN INSTANCE OF THE TABLE ----------------------------------------

# Deletes a token distribution record
@tokenomics.route('/delete_token_distribution/<int:token_distribution_id>', methods=['DELETE'])
def delete_token_distribution(token_distribution_id):
    try:
        token_distribution_to_delete = session.query(
            Token_distribution).filter_by(id=token_distribution_id).first()

        if not token_distribution_to_delete:
            return jsonify({'message': 'Token distribution not found', 'status': 404}), 404

        session.delete(token_distribution_to_delete)
        session.commit()

        return jsonify({'message': 'Token distribution deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting token distribution: {str(e)}', 'status': 500}), 500


# Deletes a token utility record
@tokenomics.route('/delete_token_utility/<int:token_utility_id>', methods=['DELETE'])
def delete_token_utility(token_utility_id):
    try:
        token_utility_to_delete = session.query(
            Token_utility).filter_by(id=token_utility_id).first()

        if not token_utility_to_delete:
            return jsonify({'message': 'Token utility not found', 'status': 404}), 404

        session.delete(token_utility_to_delete)
        session.commit()

        return jsonify({'message': 'Token utility deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting token utility: {str(e)}', 'status': 500}), 500


# Deletes a value accrual mechanism record
@tokenomics.route('/delete_value_accrual_mechanism/<int:value_accrual_mechanism_id>', methods=['DELETE'])
def delete_value_accrual_mechanism(value_accrual_mechanism_id):
    try:
        value_accrual_mechanism_to_delete = session.query(
            Value_accrual_mechanisms).filter_by(id=value_accrual_mechanism_id).first()

        if not value_accrual_mechanism_to_delete:
            return jsonify({'message': 'Value accrual mechanism not found', 'status': 404}), 404

        session.delete(value_accrual_mechanism_to_delete)
        session.commit()

        return jsonify({'message': 'Value accrual mechanism deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting value accrual mechanism: {str(e)}', 'status': 500}), 500


# Deletes a tokenomic record
@tokenomics.route('/delete_tokenomic/<int:tokenomic_id>', methods=['DELETE'])
def delete_tokenomic(tokenomic_id):
    try:
        tokenomic_to_delete = session.query(
            Tokenomics).filter_by(id=tokenomic_id).first()

        if not tokenomic_to_delete:
            return jsonify({'message': 'Tokenomic not found', 'status': 404}), 404

        session.delete(tokenomic_to_delete)
        session.commit()

        return jsonify({'message': 'Tokenomic deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting tokenomic: {str(e)}', 'status': 500}), 500
