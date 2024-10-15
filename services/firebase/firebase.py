import os
from firebase_admin import initialize_app, credentials, messaging
from typing import List, Optional
from firebase_admin import messaging

# Try the original path
original_path = os.path.abspath('services/firebase/service-account.json')
path = original_path if os.path.exists(original_path) else '/etc/secrets/service-account.json'

# Creds
cred = credentials.Certificate(path)
default_app = initialize_app(credential=cred)



def send_notification(
    topic: Optional[str],
    title: str,
    body: str,
    action: str = 'new_alert',
    type: str = "alert",
    coin: Optional[str] = None,
    timeframe: Optional[str] = None,
    web_tokens: Optional[List[str]] = None
) -> None:
    """
    Sends notifications to both mobile devices (via FCM topics) and web clients (via FCM web tokens).

    This function can send notifications to mobile devices subscribed to a specific topic
    and/or to web clients using their FCM tokens. It supports sending different types of
    notifications with custom data payloads.

    Args:
        topic (Optional[str]): The FCM topic to send the notification to for mobile devices.
            If None, no topic notification will be sent.
        title (str): The title of the notification.
        body (str): The body text of the notification.
        action (str, optional): The action category for the notification. Defaults to 'new_alert'.
        type (str, optional): The type of the notification. Defaults to "alert".
        coin (Optional[str], optional): The cryptocurrency coin related to the notification, if any.
        timeframe (Optional[str], optional): The timeframe related to the notification, if any.
        web_tokens (Optional[List[str]], optional): A list of FCM web tokens to send the notification to.
            If None, no web notifications will be sent.

    Raises:
        Exception: If there's an error sending the notification. The error message will contain details.

    Returns:
        None

    Note:
        - If both 'topic' and 'web_tokens' are provided, notifications will be sent to both channels.
        - For mobile devices, the notification is sent using FCM topics.
        - For web clients, the notification is sent using individual FCM tokens.
        - The function prints success and failure messages to the console.
    """
    try:
        data_payload = {
            "type": str(type),
            "coin": str(coin) if coin is not None else '',
            "timeframe": str(timeframe) if timeframe is not None else ''
        }

        # Preparar la notificación base
        notification = messaging.Notification(title=title, body=body)

        # Para notificaciones basadas en topic (apps móviles)
        if topic:
            message = messaging.Message(
                notification=notification,
                data=data_payload,
                topic=topic,
                android=messaging.AndroidConfig(priority='high'),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default', category=action)
                    )
                )
            )
            response = messaging.send(message)
            print(f"Successfully sent message to topic: {response}")

        # Para clientes de aplicaciones web
        if web_tokens:
            web_config = messaging.WebpushConfig(
                headers={'Urgency': 'high'},
                notification={
                    'icon': 'icon notification',
                    'click_action': '#URL ID'
                }
            )
            
            # Enviar en lotes para mayor eficiencia
            messages = [
                messaging.Message(
                    notification=notification,
                    data=data_payload,
                    token=token,
                    webpush=web_config
                ) for token in web_tokens
            ]
            
            batch_response = messaging.send_all(messages)
            print(f"Successfully sent {batch_response.success_count} messages to web clients")
            if batch_response.failure_count > 0:
                print(f"Failed to send {batch_response.failure_count} messages")

    except Exception as e:
        raise Exception(f"Error sending notification: {str(e)}")
    
    
# Example usage
# result, status_code = send_notification(
#     topic='bitcoin_4999_m1_analysis',
#     title='Cosmos Advances with Valence Integration',
#     body="""
# Cosmos (ATOM) is driving blockchain interoperability with its IBC protocol and the launch of Valence, a cross-chain protocol aimed at enhancing web3 interrelation. This initiative, combined with fee-free Bitcoin bridges and strategic partnerships, suggests a bright future for ATOM. Valence's integration is expected to bolster the interchain ecosystem, promoting wider adoption and economic efficiency, potentially stabilizing and increasing ATOM's market value.

# Despite the recent market selloff affecting ATOM, the Cosmos network’s advancements indicate resilience. Valence enhances interoperability across various crypto-native organizations, supporting token swaps and liquid restaking which would be highly valuable in generating engagement in the crypto community. It remains to be seen how the price of ATOM will develop after this addition, as it is difficult to understand the effect in a bear market for altcoins like the current one.
# """,
#     coin='bitcoin'
# )
# print(result, status_code)
