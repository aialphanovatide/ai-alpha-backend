import os
from typing import Dict, Tuple
from http import HTTPStatus
from firebase_admin import initialize_app, credentials, messaging

# Get the absolute path to the service account JSON file
json_file_path = os.path.abspath('services/firebase/service-account.json')

cred = credentials.Certificate(json_file_path)
default_app = initialize_app(credential=cred)

def send_notification(topic: str, title: str, body: str, action: str = 'new_alert', type: str = "alert", coin: str = None ) -> Tuple[Dict[str, str], int]:
    """
    Send a notification to devices subscribed to a specific topic using Firebase Cloud Messaging.

    Args:
        topic (str): The topic to which the message will be sent.
        title (str): The title of the notification.
        body (str): The body content of the notification.
        action (str, optional): The action category for iOS devices. Defaults to 'new_alert'.

    Returns:
        Tuple[Dict[str, str], int]: A tuple containing a dictionary with message, success, and error keys,
        and an HTTP status code.
    """
    response_dict = {"message": None, "success": False, "error": None}
    status_code = HTTPStatus.OK

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                "type": type,
                "coin": coin
            },
            topic=topic,
            android=messaging.AndroidConfig(
                priority='high',
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        category=action
                    )
                )
            )
        )

        response = messaging.send(message)
        
        if response:
            response_dict["message"] = f"Notification sent successfully to topic: {topic}"
            response_dict["success"] = True
        else:
            response_dict["message"] = f"Failed to send notification to topic: {topic}"
            response_dict["error"] = "No response from Firebase"
            status_code = HTTPStatus.BAD_REQUEST

    except Exception as e:
        response_dict["message"] = "Error sending notification"
        response_dict["error"] = str(e)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    return response_dict, status_code

# Example usage
# result, status_code = send_notification(
#     topic='founders_14999_m1',
#     title='NEARUSDT 4H Chart - Bullish',
#     body='Price Crossover Resistance 2'
# )
# print(result, status_code)
