from config import Topic, Notification, Session
from typing import Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from services.firebase import firebase
from services.firebase.firebase import send_notification
from datetime import datetime

notification_model = Notification


class NotificationService:
    """Service class for handling notifications and alerts."""
    def __init__(self):
        self.notification_model = notification_model
        self.types = ["alert", "support_resistance", "deep_dive", "narratives", "daily_macro", "spotlight"]

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
                        Topic.name.ilike(f"%{type}%")  # Match topics with the specified type
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
  
   

# Test
# notification_service = NotificationService()
# notification_service.push_notification(
#     coin="btc",
#     title="Test",
#     body="Test",
#     type="alert",
#     timeframe="1h"
# )