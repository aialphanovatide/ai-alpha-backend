import requests
from sqlalchemy import and_
from config import PurchasedPlan, session, CoinBot, User
from flask import jsonify, request, Blueprint
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/new_user_data', methods=['POST'])
def set_new_user():
    try:
        data = request.json
        
        new_user = User(
            nickname=data.get('nickname'),
            email=data.get('email'),
            email_verified=data.get('email_verified'),
            picture=data.get('picture'),
            auth0id=data.get('auth0id'),
            provider=data.get('provider'),
            created_at=datetime.now()
        )

        session.add(new_user)
        session.commit()
        
        return jsonify({'success': True, 'message': 'User created successfully'}), 200
                
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    
@user_bp.route('/edit_user_data/<int:user_id>', methods=['PUT'])
def edit_user_data(user_id):
    try:
        data = request.json
        
        user = session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if 'nickname' in data:
            user.nickname = data['nickname']
        if 'email' in data:
            user.email = data['email']
        if 'email_verified' in data:
            user.email_verified = data['email_verified']
        if 'picture' in data:
            user.picture = data['picture']
        if 'auth0id' in data:
            user.auth0id = data['auth0id']
        if 'provider' in data:
            user.provider = data['provider']
        if 'created_at' in data:
            user.created_at = data['created_at']

        session.commit()
        
        return jsonify({'success': True, 'message': 'User data updated successfully'}), 200
                
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/users_with_plans', methods=['GET'])
def get_all_users_with_plans():
    try:
        users = session.query(User).outerjoin(PurchasedPlan).all()
        
        result = []
        for user in users:
            user_data = {
                'user_id': user.user_id,
                'nickname': user.nickname,
                'email': user.email,
                'email_verified': user.email_verified,
                'picture': user.picture,
                'auth0id': user.auth0id,
                'provider': user.provider,
                'created_at': user.created_at,
                'purchased_plans': []
            }
            for plan in user.purchased_plans:
                plan_data = {
                    'product_id': plan.product_id,
                    'reference_name': plan.reference_name,
                    'price': plan.price,
                    'is_subscribed': plan.is_subscribed,
                    'created_at': plan.created_at
                }
                user_data['purchased_plans'].append(plan_data)
            result.append(user_data)
        
        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/user_with_plans', methods=['GET'])
def get_user_with_plans():
    try:
        user_id = request.args.get('user_id')
        email = request.args.get('email')
        nickname = request.args.get('nickname')
        
        query = session.query(User).outerjoin(PurchasedPlan)
        
        if user_id:
            user = query.filter(User.user_id == user_id).first()
        elif email:
            user = query.filter(User.email == email).first()
        elif nickname:
            user = query.filter(User.nickname == nickname).first()
        else:
            return jsonify({'success': False, 'message': 'User identifier not provided'}), 400
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'email': user.email,
            'email_verified': user.email_verified,
            'picture': user.picture,
            'auth0id': user.auth0id,
            'provider': user.provider,
            'created_at': user.created_at,
            'purchased_plans': []
        }
        for plan in user.purchased_plans:
            plan_data = {
                'product_id': plan.product_id,
                'reference_name': plan.reference_name,
                'price': plan.price,
                'is_subscribed': plan.is_subscribed,
                'created_at': plan.created_at
            }
            user_data['purchased_plans'].append(plan_data)
        
        return jsonify({'success': True, 'data': user_data}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/save_package', methods=['POST'])
def save_package():
    try:
        data = request.json
        
        new_plan = PurchasedPlan(
            reference_name=data.get('reference_name'),
            price=data.get('price'),
            is_subscribed=data.get('is_subscribed', True),
            user_id=data.get('user_id'),
            created_at=datetime.now()
        )

        session.add(new_plan)
        session.commit()
        
        return jsonify({'success': True, 'message': 'Package saved successfully'}), 200
                
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500



@user_bp.route('/unsubscribe_package/<int:product_id>', methods=['PUT'])
def unsubscribe_package(product_id):
    try:
        # Buscar el plan por ID
        plan = session.query(PurchasedPlan).filter_by(product_id=product_id).first()
        
        if not plan:
            return jsonify({'success': False, 'message': 'Package not found'}), 404
        
        # Actualizar el estado de suscripción
        plan.is_subscribed = False

        session.commit()
        
        return jsonify({'success': True, 'message': 'User unsubscribed from package successfully'}), 200
                
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
