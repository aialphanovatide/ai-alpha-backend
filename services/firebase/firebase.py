import os
from typing import Dict, Tuple
from firebase_admin import initialize_app, credentials, messaging

# Try the original path
original_path = os.path.abspath('services/firebase/service-account.json')
path = original_path if os.path.exists(original_path) else '/etc/secrets/service-account.json'

# Creds
cred = credentials.Certificate(path)
default_app = initialize_app(credential=cred)

def send_notification(topic: str, title: str, body: str, action: str = 'new_alert', type: str = "alert", coin: str = None, timeframe: str = None) -> None:
    """
    Send a notification to devices subscribed to a specific topic using Firebase Cloud Messaging.

    Args:
        topic (str): The topic to which the message will be sent.
        title (str): The title of the notification.
        body (str): The body content of the notification.
        action (str, optional): The action category for iOS devices. Defaults to 'new_alert'.
        type (str, optional): The type of notification. Defaults to "alert".
        coin (str, optional): The coin associated with the notification. Defaults to None.

    Raises:
        Exception: If there's an error sending the notification.

    Returns:
        None
    """

    try:
        # Convert type and coin to strings if they are not already
        str_type = str(type)
        str_coin = str(coin) if coin is not None else ''
        str_timeframe = str(timeframe) if timeframe is not None else ''

        data_payload = {
            "type": str_type,  # Ensure type is a string
            "coin": str_coin,  # Ensure coin is a string, handle None case
            "timeframe": str_timeframe
        }

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data_payload,
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
        print(response)

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
