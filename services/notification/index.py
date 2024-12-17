from config import Topic, Notification, Session
from typing import Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from services.firebase.firebase import send_notification
from datetime import datetime

notification_model = Notification


class NotificationService:
    """Service class for handling notifications and alerts."""

    def validate_topics(self, coin: str, type: str, timeframe: str = None) -> List[Topic]:
        """
        Validates and returns a list of topics that match the given coin and type.

        Args:
            coin (str): The coin reference to filter topics by (e.g. 'bitcoin', 'ethereum').
            type (str): The type of notification. Valid types are:
                - 'alert': For price alerts, requires timeframe
                - 'deep_dive': For in-depth analysis
                - 'narratives': For market narrative updates
                - 'support_resistance': For S&R level updates
                - 'daily_macro': For daily macro analysis
                - 'spotlight': For coin spotlights
            timeframe (str, optional): The timeframe for alerts 1h and 4h. Required when type is 'alert'.
        Returns:
            List[Topic]: A list of Topic objects that match the specified criteria.

        Raises:
            ValueError: If the notification type is invalid or no matching topics are found.
            SQLAlchemyError: If a database operation fails.
            RuntimeError: For any unexpected errors during validation.
        """
        try:
            with Session() as session:
                query = session.query(Topic)
                
                # Filter topics based on the notification type
                if type == "alert":
                    query = query.filter(
                        Topic.reference.ilike(f"%{coin}%"),  # Match topics with coin reference
                        Topic.timeframe == timeframe  # Match topics with the specified timeframe
                    )

                elif type in ["deep_dive", "narratives", "support_resistance", "daily_macro", "spotlight"]:
                    query = query.filter(
                        Topic.reference.ilike(f"%{coin}%"),  # Match topics with coin reference
                        Topic.type.ilike(f"%{type}%")  # Match topics with the specified type
                    )
                else:
                    raise ValueError(f"Invalid notification type: {type}")

                topics = query.all()
                if not topics:
                    raise ValueError(f"No topics found for coin {coin} and type {type}")

                return topics

        except SQLAlchemyError as e:
            raise
        except ValueError as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to validate topics: {str(e)}")

    def push_notification(self, coin: str, title: str, body: str, type: str, timeframe: str = None) -> None:
        """
        Push a notification for a specific coin and type.

        Raises:
            ValueError: If validation fails
            SQLAlchemyError: If database operation fails
            RuntimeError: For unexpected errors or FCM failures
        """
        try:
            # Get validated topics
            topics = self.validate_topics(coin, type, timeframe)
            date_now = datetime.now()

            with Session() as session:
                # Save notifications to database
                for topic in topics:
                    if type in ["deep_dive", "narratives", "support_resistance", "daily_macro", "spotlight"]:
                        new_notification = Notification(
                            topic_id=topic.id,
                            title=title,
                            body=body,
                            coin=coin,
                            type=type,
                            created_at=date_now,
                            updated_at=date_now
                        )
                        session.add(new_notification)
                session.commit()

                # Send FCM notifications
                failed_topics = []
                for topic in topics:
                    try:
                        send_notification(
                            topic=topic.name,
                            title=title,
                            body=body,
                            type=type,
                            coin=coin,
                            timeframe=timeframe
                        )
                    except Exception as e:
                        failed_topics.append({"topic": topic.name, "error": str(e)})

                if failed_topics:
                    raise RuntimeError(
                        f"Failed to send notifications to some topics: {failed_topics}"
                    )

        except (ValueError, SQLAlchemyError):
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to process notification: {str(e)}")
        Raises:
            RuntimeError: If FCM notification fails
        """
        try:
            # Define the query based on the notification type
            if type == "alert":
                topics = self.session.query(Topic).filter(
                    Topic.reference.ilike(f"%{coin}%"),
                    Topic.timeframe == timeframe
                ).all()
                
            elif type in ["analysis", "support_resistance"]:
                topics = self.session.query(Topic).filter(
                    Topic.reference.ilike(f"%{coin}%"),
                    Topic.name.ilike(f"%{type}%")
                ).all()
                print(topics)
            else:
                raise ValueError(f"Invalid notification type: {type}")

            if not topics:
                raise ValueError(f"No topics found for the coin {coin} and type {type}")

            for topic in topics:
                if type in ["analysis", "support_resistance"]:
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
                self._send_fcm_notification(topic.name, title, body, type, coin, timeframe)
        
        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Database error while processing notification: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Unexpected error while processing notification: {str(e)}")

    def _send_fcm_notification(self, topic: str, title: str, body: str, type: str, coin: str, timeframe: str):
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
                coin=coin,
                timeframe=timeframe
            )
        except Exception as e:
            raise RuntimeError(f"Failed to send FCM notification to topic {topic}: {str(e)}")

