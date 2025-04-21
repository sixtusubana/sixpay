from flask_login import UserMixin
from datetime import datetime as dt, date
today_raw = date.today()
today = date.isoformat(today_raw)
month = f"{ today_raw.month }-{ today_raw.year }"

# User class representing client user (for Flask-Login)
class AdminUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# class User(UserMixin):
#     def __init__(self, details):
#         self.id = details['id']
#         self.username = details['username']
#         self.name = details['name']
#         self.email = details['email']
#         self.phone = details[ 'phone' ]
#         self.status = details['status']
#         self.img = details['img']

# class User(UserMixin, db.Model):
#     __tablename__ = 'user'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(20), unique=True, nullable=False)
#     name = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(200), nullable=False)
#     password = db.Column(db.String(200), unique=False, nullable=False)
#     is_admin = db.Column(db.Boolean, nullable=True)
#     status = db.Column(db.String(50), nullable=False)
#     img = db.Column(db.String(200), nullable=True)
#
#     def __init__(self, username, name, email, status):
#         self.username = username
#         self.name = name
#         self.email = email
#         self.status = status
#
#     def obj_to_dict(self):
#         return {
#             'name': self.name,
#             'username': self.username,
#             'email': self.email,
#             'status': self.status,
#             'is_admin': self.is_admin
#         }
#
#     def set_password(self, password):
#         self.password = generate_password_hash(password, method='sha256')
#
#     def check_password(self, password):
#         return check_password_hash(self.password, password)
#
#     def __repr__(self):
#         return "<User {}>".format(self.username)
