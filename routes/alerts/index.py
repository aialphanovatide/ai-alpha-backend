import re
import sys
import logging
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from flask import jsonify, request, Blueprint
from services.notification.index import NotificationService
from config import session, Category, Alert, CoinBot, Session
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel
from redis_client.redis_client import cache_with_redis, update_cache_with_redis
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel


tradingview_bp = Blueprint(
    'tradingview_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

LOGS_SLACK_CHANNEL_ID = 'C06FTS38JRX'
notification_service = NotificationService()


def extract_timeframe(alert_name):
    """
    Extract standardized timeframe from alert name.
    Example: 'BTCUSDT 4H Chart - Bearish' -> '4h'
    
    Returns:
        str: Normalized timeframe ('1h', '4h', '1d', '1w') or None if not found
    """
    timeframe_mapping = {
        '1H': '1h', '4H': '4h', '1D': '1d', '1W': '1w',
        '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w'
    }
    
    if not alert_name:
        return None
        
    match = re.search(r'(\d+[HhDdWw])\s*[Cc]hart', alert_name)
    if match:
        timeframe = match.group(1).upper()
        return timeframe_mapping.get(timeframe)
    return None

@tradingview_bp.route('/alerts/categories', methods=['POST'])  
def get_alerts_by_categories():
    try:
        data = request.json
        if not data or 'categories' not in data:
            return jsonify({'error': 'Categories are required'}), 400

        categories = data.get('categories')
        timeframe = data.get('timeframe')
        
        # Validate timeframe if provided
        valid_timeframes = ['1h', '4h', '1d', '1w']
        if timeframe and timeframe.lower() not in valid_timeframes:
            return jsonify({'error': f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}), 400

        # Pagination validation
        try:
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 10))
        except ValueError:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        if page < 1 or per_page < 1:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        response = {
            'categories': {},
            'total_alerts': 0
        }

        for category_name in categories:
            # Query category
            category_obj = session.query(Category).filter(
                func.lower(Category.name).in_([category_name.strip().lower()]) |
                func.lower(Category.alias).in_([category_name.strip().lower()])
            ).first()

            if not category_obj:
                response['categories'][category_name] = {
                    'error': f"Category {category_name} doesn't exist",
                    'data': [],
                    'total': 0
                }
                continue

            # Build base query
            alerts_query = (session.query(Alert)
                          .join(CoinBot)
                          .filter(CoinBot.category_id == category_obj.category_id))

            # Apply timeframe filter if provided
            if timeframe:
                alerts_query = alerts_query.filter(
                    Alert.alert_name.ilike(f'%{timeframe}%chart%')
                )

            # Order by created_at descending
            alerts_query = alerts_query.order_by(desc(Alert.created_at))
            
            # Get total count
            total_category_alerts = alerts_query.count()
            response['total_alerts'] += total_category_alerts

            # Apply pagination
            alerts = alerts_query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to dict and add timeframe
            alerts_list = []
            for alert in alerts:
                alert_dict = alert.as_dict()
                alert_dict['timeframe'] = extract_timeframe(alert_dict['alert_name'])
                alerts_list.append(alert_dict)

            category_response = {
                'data': alerts_list,
                'total': total_category_alerts,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': (total_category_alerts + per_page - 1) // per_page,
                    'has_next': page < ((total_category_alerts + per_page - 1) // per_page),
                    'has_prev': page > 1
                }
            }

            response['categories'][category_name] = category_response

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
@tradingview_bp.route('/alerts/coins', methods=['POST'])
def get_filtered_alerts():
    try:
        data = request.json
        if not data or 'coins' not in data:
            return jsonify({'error': 'Coins array is required'}), 400

        coins = data.get('coins')
        timeframe = data.get('timeframe')
        
        # Validate timeframe if provided
        valid_timeframes = ['1h', '4h', '1d', '1w']
        if timeframe and timeframe.lower() not in valid_timeframes:
            return jsonify({'error': f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}), 400

        # Pagination validation
        try:
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 10))
        except ValueError:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        if page < 1 or per_page < 1:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        response = {
            'coins': {},
            'total_alerts': 0
        }

        for coin_name in coins:
            # Query coin with case-insensitive match
            coin_bot = session.query(CoinBot).filter(
                func.lower(CoinBot.name) == coin_name.strip().lower()
            ).first()

            if not coin_bot:
                response['coins'][coin_name] = {
                    'error': f'Coin {coin_name} not found',
                    'data': [],
                    'total': 0
                }
                continue

            # Build base query
            alerts_query = session.query(Alert).filter(Alert.coin_bot_id == coin_bot.bot_id)

            # Apply timeframe filter if provided
            if timeframe:
                alerts_query = alerts_query.filter(
                    Alert.alert_name.ilike(f'%{timeframe}%chart%')
                )

            # Order by created_at descending
            alerts_query = alerts_query.order_by(desc(Alert.created_at))

            # Get total count
            total_coin_alerts = alerts_query.count()
            response['total_alerts'] += total_coin_alerts

            # Apply pagination
            alerts = alerts_query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to dict and add timeframe
            alerts_list = []
            for alert in alerts:
                alert_dict = alert.as_dict()
                timeframe = extract_timeframe(alert_dict['alert_name'])
                alert_dict['timeframe'] = timeframe
                alerts_list.append(alert_dict)

            coin_response = {
                'data': alerts_list,
                'total': total_coin_alerts,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': (total_coin_alerts + per_page - 1) // per_page,
                    'has_next': page < ((total_coin_alerts + per_page - 1) // per_page),
                    'has_prev': page > 1
                }
            }

            response['coins'][coin_name] = coin_response

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    