"""Notifications (surfaces trigger-generated messages to users)."""

from config.db import fetch_all, fetch_scalar, execute


def list_for_user(user_id, limit=50):
    return fetch_all(
        """SELECT Notification_ID, Message, Status, Created_At
           FROM Notifications WHERE User_ID = :u
           ORDER BY Created_At DESC FETCH FIRST :lim ROWS ONLY""",
        {"u": user_id, "lim": limit},
    )


def unread_count(user_id):
    return fetch_scalar(
        "SELECT COUNT(*) FROM Notifications WHERE User_ID = :u AND Status = 'UNREAD'",
        {"u": user_id},
    ) or 0


def mark_read(notification_id, user_id):
    return execute(
        "UPDATE Notifications SET Status = 'READ' WHERE Notification_ID = :id AND User_ID = :u",
        {"id": notification_id, "u": user_id},
    )


def mark_all_read(user_id):
    return execute(
        "UPDATE Notifications SET Status = 'READ' WHERE User_ID = :u AND Status = 'UNREAD'",
        {"u": user_id},
    )
