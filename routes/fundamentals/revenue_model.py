from config import Revenue_model, session
from flask import Blueprint, request


revenue_model = Blueprint('revenue_model_bp', __name__)

@revenue_model.route('/revenue_model', methods=['POST'])
def post_revenue_model():

    try:
        data = request.data
        coin_bot_id = data['coin_bot_id']
        analized_revenue = data['analized_revenue']
        fees_1ys = data['fees_1ys']

        if analized_revenue or fees_1ys:
            new_revenue = Revenue_model(analized_revenue=analized_revenue,
                          fees_1ys=fees_1ys,
                          coin_bot_id=coin_bot_id
                          )
            session.add(new_revenue)
            session.commit()

        return 'Revenue model updated', 200

        
    except Exception as e:
        return f'Error posting a new revenue model: {str(e)}', 500
