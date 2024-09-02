import os
import secrets
import string
import jwt
from sqlalchemy import exc
from config import Notification, PurchasedPlan, session, User
from flask import jsonify, request, Blueprint
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from services.firebase.firebase import send_notification
from utils.general import get_users_by_group

notification_bp = Blueprint('notification', __name__)
@notification_bp.route('/send_notification', methods=['POST'])
def send_notification_route():
    """
    Endpoint to send notifications to users based on their group.

    This endpoint receives a JSON payload with the necessary information to send
    notifications to users belonging to a specified user group. The notifications
    are sent using Firebase Cloud Messaging (FCM) and are recorded in the database.

    Request JSON:
    {
        "user_group": "free_trial",  # Required. The group of users to notify.
        "title": "Notification Title",  # Required. The title of the notification.
        "body": "Notification body content",  # Required. The body content of the notification.
        "action": "new_alert",  # Optional. The action category for iOS devices. Default is 'new_alert'.
        "type": "alert",  # Optional. The type of notification. Default is 'alert'.
        "coin": "BTC"  # Optional. Additional data to include in the notification.
    }

    Returns:
        JSON response with the success status and a message indicating the result
        of the notification sending process.

    Response JSON:
    {
        "message": "Notifications sent. Successes: X, Failures: Y",
        "success": true/false
    }
    """
    data = request.json

    user_group = data.get('user_group')
    title = data.get('title')
    body = data.get('body')
    action = data.get('action', 'new_alert')
    type = data.get('type', 'alert')
    coin = data.get('coin', None)

    # Validate required fields
    if not user_group or not title or not body:
        return jsonify({"message": "User group, title, and body are required", "success": False}), 400

    # Retrieve users belonging to the specified group
    users = get_users_by_group(user_group)

    if not users:
        return jsonify({"message": f"No users found for group: {user_group}", "success": False}), 404

    # Initialize counters for success and failure
    success_count = 0
    failure_count = 0

    # Send notification to each user in the group
    for user in users:
        # Use the user's auth0id as the topic for the notification
        topic = user.auth0id
        response, status_code = send_notification(topic, title, body, action, type, coin)
        
        if response["success"]:
            success_count += 1
            # Record the successful notification in the database
            notification = Notification(
                topic=topic,
                message=body
            )
            session.add(notification)
        else:
            failure_count += 1
            print(f"Failed to send notification to user {user.auth0id}: {response['error']}")

    # Commit the transaction to save notifications in the database
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error committing to database: {str(e)}")

    # Return a summary of the notification sending process
    return jsonify({
        "message": f"Notifications sent. Successes: {success_count}, Failures: {failure_count}",
        "success": success_count > 0
    }), 200