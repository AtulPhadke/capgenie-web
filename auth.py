from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Simple in-memory user storage (in production, use a database)
# You can change these credentials as needed
USERS = {
    'admin': User(1, 'admin', generate_password_hash('capgenie2024')),
    'user1': User(2, 'user1', generate_password_hash('password123')),
    'researcher': User(3, 'researcher', generate_password_hash('science2024'))
}

def get_user(username):
    """Get user by username"""
    return USERS.get(username)

def verify_user(username, password):
    """Verify user credentials"""
    user = get_user(username)
    if user and check_password_hash(user.password_hash, password):
        return user
    return None

def add_user(username, password):
    """Add a new user (for admin purposes)"""
    if username not in USERS:
        user_id = len(USERS) + 1
        USERS[username] = User(user_id, username, generate_password_hash(password))
        return True
    return False 