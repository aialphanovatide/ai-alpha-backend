from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON, Enum
from sqlalchemy.sql import func
from config import Base 
import enum

class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class NotificationPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Notification(Base):
    """
    Represents a notification in the admin dashboard.

    This class defines the structure for storing and managing notifications.

    Attributes:
        id (int): The primary key for the notification.
        type (str): The type of notification (e.g., 'system_alert', 'user_action', 'maintenance').
        message (str): The content of the notification message.
        created_at (datetime): Timestamp of when the notification was created.
        status (enum): The current status of the notification (pending, sent, failed).
        priority (enum): The priority level of the notification.
        recipient_group (str): The group of users who should receive the notification.
        sent_count (int): Number of recipients the notification was successfully sent to.
        error_count (int): Number of failed attempts to send the notification.
        related_object_type (str): The type of object related to this notification.
        related_object_id (int): The ID of the related object.
        additional_data (JSON): Additional data related to the notification, stored as JSON.
    """
    __tablename__ = 'admin_notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    recipient_group = Column(String, default='all_users', nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    related_object_type = Column(String, nullable=True)
    related_object_id = Column(Integer, nullable=True)
    additional_data = Column(JSON, nullable=True)

    def __init__(self, type, message, recipient_group='all_users', priority=NotificationPriority.MEDIUM, 
                 related_object_type=None, related_object_id=None, additional_data=None):
        """
        Initialize a new Notification instance.

        Args:
            type (str): The type of notification.
            message (str): The content of the notification message.
            recipient_group (str, optional): The group of users who should receive the notification. Defaults to 'all_users'.
            priority (NotificationPriority, optional): The priority level of the notification.
            related_object_type (str, optional): The type of object related to this notification.
            related_object_id (int, optional): The ID of the related object.
            additional_data (dict, optional): Additional data related to the notification.
        """
        self.type = type
        self.message = message
        self.recipient_group = recipient_group
        self.priority = priority
        self.related_object_type = related_object_type
        self.related_object_id = related_object_id
        self.additional_data = additional_data

    def to_dict(self):
        """
        Convert the Notification object to a dictionary.

        Returns:
            dict: A dictionary representation of the Notification.
        """
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'priority': self.priority.value,
            'recipient_group': self.recipient_group,
            'sent_count': self.sent_count,
            'error_count': self.error_count,
            'related_object_type': self.related_object_type,
            'related_object_id': self.related_object_id,
            'additional_data': self.additional_data
        }

    def mark_as_sent(self):
        """Mark the notification as sent and increment the sent count."""
        self.status = NotificationStatus.SENT
        self.sent_count += 1

    def mark_as_failed(self):
        """Mark the notification as failed and increment the error count."""
        self.status = NotificationStatus.FAILED
        self.error_count += 1


# Usage example:
# new_notification = Notification(
#     type="system_alert",
#     message="System maintenance scheduled",
#     recipient_group="admin_users",
#     priority=NotificationPriority.HIGH,
#     additional_data={"maintenance_duration": "2 hours"}
# )