from flask import current_app
from config import Topic, Notification, Session
from typing import Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from services.firebase.firebase import send_notification
from datetime import datetime

class NotificationService:
    """Service class for handling notifications and alerts."""

    def validate_topics(self, coin: str, type: str, timeframe: str = None) -> List[Topic]:
        """
        Validates and returns a list of topics that match the given coin and type. This method queries the database to find topics that are relevant to the specified coin and notification type. It filters topics based on the notification type, coin reference, and timeframe (if applicable).

        Args:
            coin (str): The coin reference to filter topics by.
            type (str): The type of notification to filter topics by. Supported types are "alert", "analysis", and "s_and_r".
            timeframe (str, optional): The timeframe to filter topics by, applicable only for "alert" type. Defaults to None.

        Returns:
            List[Topic]: A list of Topic objects that match the specified coin and type.

        Raises:
            ValueError: If the notification type is invalid or no topics are found that match the specified coin and type.
            SQLAlchemyError: If a database operation fails during the validation process.
            RuntimeError: For any unexpected errors that occur during the validation process.
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
                elif type in ["analysis", "s_and_r"]:
                    query = query.filter(
                        Topic.reference.ilike(f"%{coin}%"),  # Match topics with coin reference
                        Topic.name.ilike(f"%{type}%")  # Match topics with the specified type
                    )
                else:
                    raise ValueError(f"Invalid notification type: {type}")

                topics = query.all()
                if not topics:
                    raise ValueError(f"No topics found for coin {coin} and type {type}")
                
                return topics

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error while validating topics: {str(e)}")
            raise
        except ValueError as e:
            raise
        except Exception as e:
            current_app.logger.error(f"Unexpected error while validating topics: {str(e)}")
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
            current_app.logger.debug(f"Starting push notification for coin: {coin}, type: {type}")
            
            # Get validated topics
            topics = self.validate_topics(coin, type, timeframe)
            date_now = datetime.now()

            with Session() as session:
                # Save notifications to database
                for topic in topics:
                    if type in ["analysis", "s_and_r"]:
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
                        current_app.logger.info(f"{type.capitalize()} saved for coin {coin} under topic {topic.name}")

                session.commit()
                current_app.logger.info(f"Successfully saved {type} notification for coin {coin}")

                # Send FCM notifications
                failed_topics = []
                for topic in topics:
                    try:
                        self._send_fcm_notification(
                            topic.name, title, body, type, coin, timeframe
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
            current_app.logger.error(f"Unexpected error while processing notification: {str(e)}")
            raise RuntimeError(f"Failed to process notification: {str(e)}")

    def _send_fcm_notification(self, topic: str, title: str, body: str, type: str, 
                             coin: str, timeframe: str) -> None:
        """
        Send a notification via Firebase Cloud Messaging.

        Raises:
            RuntimeError: If FCM notification fails
        """
        try:
            current_app.logger.debug(f"Sending FCM notification to topic: {topic}")
            send_notification(
                topic=topic,
                title=title,
                body=body,
                type=type,
                coin=coin,
                timeframe=timeframe
            )
            current_app.logger.info(f"FCM notification sent successfully for topic {topic}")
        except Exception as e:
            current_app.logger.error(f"Failed to send FCM notification to topic {topic}: {str(e)}")
            raise RuntimeError(f"Failed to send FCM notification to topic {topic}: {str(e)}")