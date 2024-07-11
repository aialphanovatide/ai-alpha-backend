from firebase_admin import initialize_app, credentials, messaging
import os

# Get the absolute path to the service account JSON file
json_file_path = os.path.abspath('services/firebase/ai-alpha-app-firebase-service-account.json')

cred = credentials.Certificate(json_file_path)
default_app = initialize_app(credential=cred)

# send messages
def send_notification(topic, title, body, action='new_alert'):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            # Targeting all devices subscribed to the topic "all"
            topic=topic,
            # Additional parameters for Android
            android=messaging.AndroidConfig(
                priority='high',
            ),
            # Additional parameters for iOS
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
        return True if response else False
    
    except Exception as e:
        print('Error sending message:', str(e))
        return None
    

# example usage
print(send_notification(topic='boostlayer_4999_m1', title='test - NEARUSDT 4H Chart - Bullish', body='Price Crossover Resistance 2'))

