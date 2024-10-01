from config import Alert, Topic,Notification
from services.firebase.firebase import send_notification
import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


notification_model = Notification

class Notification:

    def __init__(self, session: Session):
        self.session = session

    def push_notification(self, coin: str, title: str, body: str, type: str, temporality: str):
        """
        Search the Topic table for topics whose reference array contains the coin provided.
        Then, save data into either the Alert or Notification table, and trigger FCM notifications.
        
        Parameters:
        - coin: The coin associated with the notification.
        - title: The title of the notification.
        - body: The body content of the notification.
        - type: The notification type ("alert" or "analysis").
        - temporality: Temporality of the alert (e.g., 1h, 4h).
        """
        
        try:
            # Search for topics that contain the coin in the reference array
            topics = self.session.query(Topic).filter(Topic.reference.contains(coin)).all()
            
            if not topics:
                raise ValueError(f"No topics found for the coin {coin}")

            for topic in topics:
                if type == "alert":
                    # Save in the Alert table
                    new_alert = Alert(
                        topic_id=topic.id,
                        title=title,
                        body=body,
                        coin=coin,
                        temporality=temporality
                    )
                    self.session.add(new_alert)
                    print(f"Alert saved for coin {coin} under topic {topic.name}")
                
                elif type == "analysis":
                    # Save in the Notification table
                    new_notification = notification_model( 
                        topic_id=topic.id,
                        title=title,
                        body=body,
                        coin=coin
                    )
                    self.session.add(new_notification)
                    print(f"Analysis saved for coin {coin} under topic {topic.name}")
                
                else:
                    raise ValueError(f"Invalid notification type: {type}")

            # Commit the changes to the database
            self.session.commit()
            print(f"Successfully saved {type} notification for coin {coin}.")

            # Trigger FCM notification after saving
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