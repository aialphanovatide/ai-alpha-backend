from config import Revenue_model, Session, session, CoinBot
from flask import Blueprint, jsonify, request


revenue_model_bp = Blueprint('revenue_model_bp', __name__)

# Creates a revenue model
@revenue_model_bp.route('/api/create_revenue_model', methods=['POST'])
def post_revenue_model():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')

        if not coin_bot_id:
            return jsonify({'message': 'Coin ID missing', 'status': 400}), 400 

        new_revenue = Revenue_model(
            analized_revenue=data.get('analized_revenue'),
            fees_1ys=data.get('fees_1ys'),
            coin_bot_id=coin_bot_id
        )
        session.add(new_revenue)
        session.commit()
        return jsonify({'message': 'Revenue model created successfully', 'status': 200}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error creating revenue model: {str(e)}', 'status': 500}), 500


# Gets the revenue of a coin
@revenue_model_bp.route('/api/get_revenue_models', methods=['GET'])
def get_revenue_models():
    try:
        coin_id = request.args.get('coin_id')
        coin_name = request.args.get('coin_name')

        if not coin_id and not coin_name:
            return jsonify({'message': 'Coin ID or name is required', 'status': 400}), 400
        
        coin_data = None

        if coin_name:
            coin = session.query(CoinBot).filter(CoinBot.bot_name==coin_name).first()
            coin_data = session.query(Revenue_model).filter_by(coin_bot_id=coin.bot_id).first() if coin else None
           
        if coin_id:
            coin = session.query(Revenue_model).filter_by(coin_bot_id=coin_id).first()
            coin_data = coin if coin else None

        if coin_data == None:
            return jsonify({'message': 'No revenue model found', 'status': 404}), 404
        
        revenue_model = coin_data.as_dict()
        return jsonify({'revenue_model': revenue_model, 'status': 200}), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error getting revenue models: {str(e)}', 'status': 500}), 500



@revenue_model_bp.route('/api/edit_revenue_model/<int:model_id>', methods=['PUT'])
def edit_revenue_model(model_id):
    try:
        data = request.json
        updated_analized_revenue = data.get('analized_revenue')
        updated_fees_1ys = data.get('fees_1ys', None)

        with Session() as session:
            revenue_model = session.query(Revenue_model).filter_by(coin_bot_id=model_id).first()

            if revenue_model:
                revenue_model.analized_revenue = updated_analized_revenue
                revenue_model.fees_1ys = updated_fees_1ys
                session.commit()
                return jsonify({'message': 'Revenue model updated successfully'}), 200
            else:
                return jsonify({'error': 'Revenue model not found'}), 404

    except Exception as e:
        return jsonify({'error': f'Error editing revenue model: {str(e)}'}), 500
