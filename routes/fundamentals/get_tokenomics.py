from flask import Blueprint, request, jsonify
from config import Tokenomics, Token_distribution, Token_utility, Value_accrual_mechanisms, Session
from sqlalchemy.orm import joinedload

get_coin_bot_tokenomics = Blueprint('getCoinBotTokenomics', __name__)

@get_coin_bot_tokenomics.route('/get_coin_bot_tokenomics/<int:coin_bot_id>', methods=['GET'])
def get_tokenomics(coin_bot_id):
    try:
        with Session() as session:
            # Realizar una consulta para obtener los tokenomics del Coin Bot específico
            tokenomics = (
                session.query(Tokenomics)
                .options(joinedload(Tokenomics.coin_bot))
                .filter_by(coin_bot_id=coin_bot_id) 
                .first()
            )

            if tokenomics:
                # Obtener información de token_distribution
                token_distribution_info = (
                    session.query(Token_distribution)
                    .filter_by(coin_bot_id=coin_bot_id)
                    .first()
                )

                # Obtener información de token_utility
                token_utility_info = (
                    session.query(Token_utility)
                    .filter_by(coin_bot_id=coin_bot_id)
                    .first()
                )

                # Obtener información de value_accrual_mechanisms
                value_accrual_mechanisms_info = (
                    session.query(Value_accrual_mechanisms)
                    .filter_by(coin_bot_id=coin_bot_id)
                    .first()
                )

                # Devolver la información de los tokenomics, token_distribution, token_utility y value_accrual_mechanisms en formato JSON
                return jsonify({
                    'coinBotInfo': {
                        'totalSupply': tokenomics.total_supply,
                        'circulatingSupply': tokenomics.circulating_supply,
                        'percentCirculatingSupply': tokenomics.percentage_circulating_supply,
                        'maxSupply': tokenomics.max_supply,
                        'supplyModel': tokenomics.supply_model,
                        'tokenDistribution': {
                            'holderCategory': token_distribution_info.holder_category,
                            'percentageHeld': token_distribution_info.percentage_held
                        },
                        'tokenUtility': {
                            'gasFeesAndTransactionSettlement': token_utility_info.gas_fees_and_transaction_settlement
                        },
                        'valueAccrualMechanisms': {
                            'tokenBurning': value_accrual_mechanisms_info.token_burning,
                            'tokenBuyback': value_accrual_mechanisms_info.token_buyback
                        }
                    }
                })
            else:
                return jsonify({'error': 'Tokenomics not found for the specified Coin Bot'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
