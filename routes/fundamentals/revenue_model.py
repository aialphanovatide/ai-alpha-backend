from config import Revenue_model, Session, session
from flask import Blueprint, jsonify, request


revenue_model_bp = Blueprint('revenue_model_bp', __name__)

@revenue_model_bp.route('/api/create_revenue_model', methods=['POST'])
def post_revenue_model():
    try:
        data = request.json
        print(data)
        coin_bot_id = data.get('coin_bot_id')

        new_revenue = Revenue_model(
            analized_revenue=data.get('analized_revenue'),
            fees_1ys=data.get('fees_1ys'),
            coin_bot_id=coin_bot_id
        )
        with Session() as session:
            session.add(new_revenue)
            session.commit()
        return jsonify({'message': 'Content created successfully'}), 200
        
    except Exception as e:
        return {'error': f'Error creating content: {str(e)}'}, 500


@revenue_model_bp.route('/api/get_revenue_models', methods=['GET'])
def get_revenue_models():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        print(coin_bot_id)
        if coin_bot_id is None:
            return 'Coin is required and must be a non-empty string containing only digits', 400

        revenue_models = session.query(Revenue_model).filter_by(coin_bot_id=coin_bot_id).all()
        print('revenue_models',revenue_models)
        
        revenue_models_list = [revenue_model.as_dict() for revenue_model in revenue_models]
        print('revenue_models_list', revenue_models_list)
        
        return {'revenue_models': revenue_models_list}, 200
    except Exception as e:
        return f'Error getting revenue models: {str(e)}', 500
