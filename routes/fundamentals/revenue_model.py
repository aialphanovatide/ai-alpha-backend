# from config import Revenue_model, Session, CoinBot
# from flask import Blueprint, jsonify, request


# revenue_model_bp = Blueprint('revenue_model_bp', __name__)

# # Creates a revenue model
# @revenue_model_bp.route('/api/create_revenue_model', methods=['POST'])
# def post_revenue_model():
#     """
#     Creates a revenue model with flexible input types.
    
#     Expected JSON payload:
#     {
#         "coin_bot_id": int,          # Must be integer
#         "analized_revenue": any,     # Can be number or string
#         "fees_1ys": any             # Can be number or string
#     }
#     """
#     with Session() as session:
#         try:
#             data = request.json
#             coin_bot_id = data.get('coin_bot_id')

#             if not coin_bot_id:
#                 return jsonify({'message': 'Coin ID missing', 'status': 400}), 400 

#             # Ensure coin_bot_id is an integer
#             try:
#                 coin_bot_id = int(coin_bot_id)
#             except (ValueError, TypeError):
#                 return jsonify({'message': 'coin_bot_id must be an integer', 'status': 400}), 400

#             # Convert values to string to ensure they can be stored
#             analized_revenue = str(data.get('analized_revenue')) if data.get('analized_revenue') is not None else None
#             fees_1ys = str(data.get('fees_1ys')) if data.get('fees_1ys') is not None else None

#             new_revenue = Revenue_model(
#                 analized_revenue=analized_revenue,
#                 fees_1ys=fees_1ys,
#                 coin_bot_id=coin_bot_id
#             )
            
#             session.add(new_revenue)
#             session.commit()
            
#             return jsonify({
#                 'message': 'Revenue model created successfully', 
#                 'status': 200,
#                 'data': new_revenue.as_dict()
#             }), 200
            
#         except Exception as e:
#             session.rollback()
#             return jsonify({
#                 'message': f'Error creating revenue model: {str(e)}', 
#                 'status': 500
#             }), 500


# # Gets the revenue of a coin
# @revenue_model_bp.route('/api/get_revenue_models', methods=['GET'])
# def get_revenue_models():
#     try:
#         coin_id = request.args.get('coin_id')
#         coin_name = request.args.get('coin_name')

#         if not coin_id and not coin_name:
#             return jsonify({'message': 'Coin ID or name is required', 'status': 400}), 400
        
#         coin_data = None

#         if coin_name:
#             coin = session.query(CoinBot).filter(CoinBot.name==coin_name).first()
#             coin_data = session.query(Revenue_model).filter_by(coin_bot_id=coin.bot_id).first() if coin else None
           
#         if coin_id:
#             coin = session.query(Revenue_model).filter_by(coin_bot_id=coin_id).first()
#             coin_data = coin if coin else None

#         if coin_data == None:
#             return jsonify({'message': 'No revenue model found', 'status': 404}), 404
        
#         revenue_model = coin_data.as_dict()
#         return jsonify({'revenue_model': revenue_model, 'status': 200}), 200
    
#     except Exception as e:
#         session.rollback()
#         return jsonify({'message': f'Error getting revenue models: {str(e)}', 'status': 500}), 500


# # Edits a revenue model
# @revenue_model_bp.route('/api/edit_revenue_model/<int:model_id>', methods=['PUT'])
# def edit_revenue_model(model_id):
#     try:
#         data = request.json
#         updated_analized_revenue = data.get('analized_revenue')
#         updated_fees_1ys = data.get('fees_1ys', None)

#         with Session() as session:
#             revenue_model = session.query(Revenue_model).filter_by(coin_bot_id=model_id).first()

#             if revenue_model:
#                 revenue_model.analized_revenue = updated_analized_revenue
#                 revenue_model.fees_1ys = updated_fees_1ys
#                 session.commit()
#                 return jsonify({'message': 'Revenue model updated successfully'}), 200
#             else:
#                 return jsonify({'error': 'Revenue model not found'}), 404

#     except Exception as e:
#         return jsonify({'error': f'Error editing revenue model: {str(e)}'}), 500


from flask import Blueprint, jsonify, request
from config import Revenue_model, Session
from sqlalchemy.exc import SQLAlchemyError

revenue_model_bp = Blueprint('revenue_model_bp', __name__)

@revenue_model_bp.route('/revenue_model', methods=['POST'])
def post_revenue_model():
    """Create a revenue model for a coin"""
    response = {'success': False, 'message': None, 'data': None}
    
    with Session() as session:
        try:
            data = request.json
            coin_id = data.get('coin_id')
            analized_revenue = data.get('analized_revenue')

            if not coin_id:
                response['message'] = 'coin_id is required'
                return jsonify(response), 400

            if not analized_revenue:
                response['message'] = 'analized_revenue is required'
                return jsonify(response), 400

            # Check if revenue model already exists
            existing_model = session.query(Revenue_model).filter_by(coin_bot_id=coin_id).first()
            if existing_model:
                response['message'] = 'Revenue model already exists for this coin'
                return jsonify(response), 409

            new_revenue = Revenue_model(
                coin_bot_id=coin_id,
                analized_revenue=analized_revenue,
                dynamic=data.get('dynamic', False)
            )
            
            session.add(new_revenue)
            session.commit()
            
            response['success'] = True
            response['message'] = 'Revenue model created successfully'
            response['data'] = new_revenue.as_dict()
            return jsonify(response), 201

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500

@revenue_model_bp.route('/revenue_model/<int:coin_id>', methods=['GET'])
def get_revenue_model(coin_id):
    """Get revenue model by coin ID"""
    response = {'success': False, 'message': None, 'data': None}
    
    with Session() as session:
        try:
            revenue_model = session.query(Revenue_model).filter_by(coin_bot_id=coin_id).first()
            
            if not revenue_model:
                response['message'] = 'No revenue model found for this coin'
                return jsonify(response), 404

            response['success'] = True
            response['data'] = revenue_model.as_dict()
            return jsonify(response), 200

        except SQLAlchemyError as e:
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500

@revenue_model_bp.route('/revenue_model/<int:coin_id>', methods=['PUT'])
def edit_revenue_model(coin_id):
    """Update revenue model for a specific coin"""
    response = {'success': False, 'message': None, 'data': None}
    
    with Session() as session:
        try:
            data = request.json
            analized_revenue = data.get('analized_revenue')

            if not analized_revenue:
                response['message'] = 'analized_revenue is required'
                return jsonify(response), 400

            revenue_model = session.query(Revenue_model).filter_by(coin_bot_id=coin_id).first()
            if not revenue_model:
                response['message'] = 'No revenue model found for this coin'
                return jsonify(response), 404

            revenue_model.analized_revenue = analized_revenue
            if 'dynamic' in data:
                revenue_model.dynamic = data['dynamic']

            session.commit()
            
            response['success'] = True
            response['message'] = 'Revenue model updated successfully'
            response['data'] = revenue_model.as_dict()
            return jsonify(response), 200

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
