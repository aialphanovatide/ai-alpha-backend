from config import Alert, Topic, Notification
from services.firebase.firebase import send_notification
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

notification_model = Notification

class Notification:

    def __init__(self, session: Session):
        self.session = session

    def push_notification(self, coin: str, title: str, body: str, type: str, timeframe: str):
        """
        Push a notification for a specific coin and type.

        This method creates and saves a notification or alert in the database,
        and then sends it via Firebase Cloud Messaging (FCM).

        Parameters:
        - coin (str): The cryptocurrency coin symbol.
        - title (str): The title of the notification.
        - body (str): The body content of the notification.
        - type (str): The type of notification ('alert', 'analysis', or 's_and_r').
        - temporality (str): The time frame for the notification (used for alerts).

        Raises:
        - ValueError: If an invalid notification type is provided or no topics are found.
        - SQLAlchemyError: If there's an error during database operations.
        - Exception: For any other unexpected errors during the process.
        """
        try:
            # Define the query based on the notification type
            if type == "alert":
                topics = self.session.query(Topic).filter(
                    Topic.reference.ilike(f"%{coin}%"),
                    Topic.timeframe == timeframe
                ).all()
                
            elif type in ["analysis", "s_and_r"]:
                topics = self.session.query(Topic).filter(
                    Topic.reference.ilike(f"%{coin}%"),
                    Topic.name.ilike(f"%{type}%")
                ).all()
               
            else:
                raise ValueError(f"Invalid notification type: {type}")

            if not topics:
                raise ValueError(f"No topics found for the coin {coin} and type {type}")

            for topic in topics:
                if type in ["analysis", "s_and_r"]:
                    new_notification = notification_model( 
                        topic_id=topic.id,
                        title=title,
                        body=body,
                        coin=coin,
                        type=type 
                    )
                    self.session.add(new_notification)
                    print(f"{type.capitalize()} saved for coin {coin} under topic {topic.name}")

            self.session.commit()
            print(f"Successfully saved {type} notification for coin {coin}.")

            for topic in topics:
                self._send_fcm_notification(topic.name, title, body, type, coin)
        
        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Database error while processing notification: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Unexpected error while processing notification: {str(e)}")

    def _send_fcm_notification(self, topic: str, title: str, body: str, type: str, coin: str):
        """
        Trigger Firebase Cloud Messaging (FCM) to send a notification.
        
        Parameters:
        - topic: The topic to which the message will be sent.
        - title: The title of the notification.
        - body: The body content of the notification.
        - type: The type of the notification ("alert" or "analysis").
        - coin: The coin associated with the notification.
        """
        try:
            # Use the send_notification function you provided
            send_notification(
                topic=topic,
                title=title,
                body=body,
                type=type,
                coin=coin
            )
            print(f"FCM notification sent successfully for topic {topic}.")
        except Exception as e:
            print(f"Failed to send FCM notification: {str(e)}")