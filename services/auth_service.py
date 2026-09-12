"""Authentication business logic."""

from werkzeug.security import check_password_hash

from config.db import fetch_one, fetch_all


def get_user_roles(user_id):
    """Return the list of role names assigned to a user."""
    rows = fetch_all(
        """
        SELECT r.Role_Name
        FROM User_Role_Assignment ura
        JOIN User_Roles r ON ura.Role_ID = r.Role_ID
        WHERE ura.UserID = :p_user
        ORDER BY r.Role_Name
        """,
        {"p_user": user_id},
    )
    return [r["role_name"] for r in rows]


def authenticate(email, password):
    """Validate credentials. Returns a user dict on success, else None."""
    user = fetch_one(
        """
        SELECT UserID, FName, LName, Email, Password_Hash, Is_Active
        FROM HEBAS_Users
        WHERE LOWER(Email) = LOWER(:email)
        """,
        {"email": email},
    )
    if not user or not user["is_active"]:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None

    roles = get_user_roles(user["userid"])
    return {
        "user_id": user["userid"],
        "name": f"{user['fname']} {user['lname']}",
        "email": user["email"],
        "roles": roles,
        "primary_role": roles[0] if roles else None,
    }
