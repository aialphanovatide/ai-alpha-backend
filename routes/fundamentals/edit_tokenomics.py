from flask import Blueprint, jsonify, request
from config import Session as DBSession 
from config import Tokenomics, Token_distribution, Token_utility, Value_accrual_mechanisms


edit_tokenomics_bp = Blueprint('editTokenomics', __name__)

@edit_tokenomics_bp.route('/save_tokenomics', methods=['POST'])
def save_tokenomics():
    data = request.json
    coin_bot_id = data.get('coinBotId')
    with DBSession() as db_session:

        # Actualizar la fila en la tabla Tokenomics
        tokenomics_data = {
            'total_supply': data.get('totalSupply'),
            'circulating_supply': data.get('circulatingSupply'),
            'percentage_circulating_supply': data.get('percentCirculatingSupply'),
            'max_supply': data.get('maxSupply'),
            'supply_model': data.get('supplyModel'),
            'coin_bot_id': coin_bot_id
        }

        tokenomics = db_session.query(Tokenomics).filter(Tokenomics.coin_bot_id == coin_bot_id).first()
        if tokenomics:
            tokenomics.total_supply = tokenomics_data['total_supply']
            tokenomics.circulating_supply = tokenomics_data['circulating_supply']
            tokenomics.percentage_circulating_supply = tokenomics_data['percentage_circulating_supply']
            tokenomics.max_supply = tokenomics_data['max_supply']
            tokenomics.supply_model = tokenomics_data['supply_model']
        else:
            new_tokenomics = Tokenomics(**tokenomics_data)
            db_session.add(new_tokenomics)

        # Actualizar la fila en la tabla TokenDistribution
        token_distribution_data = {
            'holder_category': data.get('tokenDistribution').get('holderCategory'),
            'percentage_held': data.get('tokenDistribution').get('percentageHeld'),
            'coin_bot_id': coin_bot_id
        }

        token_distribution = db_session.query(Token_distribution).filter(Token_distribution.coin_bot_id == coin_bot_id).first()
        if token_distribution:
            token_distribution.holder_category = token_distribution_data['holder_category']
            token_distribution.percentage_held = token_distribution_data['percentage_held']
        else:
            new_token_distribution = Token_distribution(**token_distribution_data)
            db_session.add(new_token_distribution)

        # Actualizar la fila en la tabla TokenUtility
        token_utility_data = {
            'gas_fees_and_transaction_settlement': data.get('tokenUtility', {}).get('gasFeesAndTransactionSettlement'),
            'coin_bot_id': coin_bot_id
        }

        token_utility = db_session.query(Token_utility).filter(Token_utility.coin_bot_id == coin_bot_id).first()
        if token_utility:
            token_utility.gas_fees_and_transaction_settlement = token_utility_data['gas_fees_and_transaction_settlement']
        else:
            new_token_utility = Token_utility(**token_utility_data)
            db_session.add(new_token_utility)

        # Actualizar la fila en la tabla ValueAccrualMechanisms
        value_accrual_mechanisms_data = {
            'token_burning': data.get('valueAccrualMechanisms', {}).get('tokenBurning'),
            'token_buyback': data.get('valueAccrualMechanisms', {}).get('tokenBuyback'),
            'coin_bot_id': coin_bot_id
        }

        value_accrual_mechanisms = db_session.query(Value_accrual_mechanisms).filter(Value_accrual_mechanisms.coin_bot_id == coin_bot_id).first()
        if value_accrual_mechanisms:
            value_accrual_mechanisms.token_burning = value_accrual_mechanisms_data['token_burning']
            value_accrual_mechanisms.token_buyback = value_accrual_mechanisms_data['token_buyback']
        else:
            new_value_accrual_mechanisms = Value_accrual_mechanisms(**value_accrual_mechanisms_data)
            db_session.add(new_value_accrual_mechanisms)

        db_session.commit()
        
        response_data = {'success': True, 'message': 'Data saved successfully'}
        return jsonify(response_data)
            