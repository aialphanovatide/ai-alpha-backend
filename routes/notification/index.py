from flask import Blueprint, request, jsonify
from sqlalchemy import desc, asc, literal, union_all, select
from sqlalchemy.exc import SQLAlchemyError
from config import Session, Alert, Notification

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Get paginated notifications and alerts with filtering and sorting options.
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        order (str): Sort order - 'asc' or 'desc' (default: 'desc')
        type (str): Filter by type (alert, analysis, etc.)
        
    Returns:
        JSON response with combined notifications/alerts data and pagination metadata
    """
    with Session() as session:
        try:
            # Parse and validate query parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            order = request.args.get('order', 'desc')
            notification_type = request.args.get('type')

            if page < 1:
                return jsonify({'error': 'Page number must be greater than 0'}), 400
                
            if per_page < 1:
                return jsonify({'error': 'Per page must be greater than 0'}), 400
                
            if order not in ['asc', 'desc']:
                return jsonify({'error': 'Order must be either "asc" or "desc"'}), 400

            # Create subqueries for notifications and alerts
            notifications_query = select([
                Notification.id.label('id'),
                Notification.title.label('title'),
                Notification.body.label('body'),
                Notification.type.label('type'),
                Notification.coin.label('symbol'),
                Notification.created_at.label('created_at'),
                Notification.updated_at.label('updated_at'),
                literal('notification').label('source')
            ])

            alerts_query = select([
                Alert.alert_id.label('id'),
                Alert.alert_name.label('title'),
                Alert.alert_message.label('body'),
                literal('alert').label('type'),
                Alert.symbol.label('symbol'),
                Alert.created_at.label('created_at'),
                Alert.updated_at.label('updated_at'),
                literal('alert').label('source')
            ])

            # Apply type filter if provided
            if notification_type:
                if notification_type == 'alert':
                    combined_query = alerts_query
                else:
                    notifications_query = notifications_query.where(
                        Notification.type == notification_type
                    )
                    combined_query = notifications_query
            else:
                # Combine queries using union_all
                combined_query = union_all(notifications_query, alerts_query)

            # Create a subquery to handle sorting
            subquery = combined_query.alias('combined')
            query = session.query(subquery)

            # Apply sorting
            sort_column = subquery.c.created_at
            if order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))

            # Get total count for pagination
            total_items = query.count()
            total_pages = (total_items + per_page - 1) // per_page

            # Apply pagination
            offset = (page - 1) * per_page
            results = query.offset(offset).limit(per_page).all()

            # Prepare response data
            items_data = []
            for item in results:
                item_dict = {
                    'notification_id': item.id,
                    'title': item.title,
                    'content': item.body,
                    'type': item.type,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None
                }
                items_data.append(item_dict)

            response = {
                'data': items_data,
                'pagination': {
                    'page': page,
                    'limit': per_page,
                    'total_pages': total_pages,
                    'total_items': total_items
                }
            }

            return jsonify(response), 200

        except SQLAlchemyError as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
