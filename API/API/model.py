# from flask import current_app
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import sha256_crypt
from datetime import datetime as dt, date
import uuid


today_raw = date.today()
today = date.isoformat(today_raw)
month = f"{today_raw.month}-{today_raw.year}"
from sqlalchemy.orm import relationship


class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    firstname = db.Column(db.Text, nullable=False)
    surname = db.Column(db.Text, nullable=False)
    account_number = db.Column(db.Integer, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    balance = db.Column(db.Float, nullable=True, default=0)
    bonus_balance = db.Column(db.Float, nullable=True, default=0)
    code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    refferal_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default="ACTIVE")
    game_on = db.Column(db.Boolean, default=False, nullable=True)
    date_registered = db.Column(db.DateTime, default=dt.now())
    verification_code = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.Text, nullable=False)
    gamify = relationship('Gamify', backref='client')
    bonus_wallet = relationship('BonusWallet', backref='client')
    transaction = relationship('Transaction', backref='client')
    wallet_transaction = relationship('WalletTransaction', backref='client')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_verification_code(self, verification_code):
        self.verification_code = sha256_crypt.encrypt(verification_code)

    def check_verification_code(self, verification_code):
        return sha256_crypt.verify(verification_code, self.verification_code)

    def to_dict(self):
        data = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        data['gamify'] = [gg.to_dict() for gg in self.gamify]
        data[ 'bonus_wallet' ] = len(self.bonus_wallet)
        data[ 'refferals' ] = Client.query.filter_by(refferal_id=self.id).count() or Client.query.filter_by(refferal_id=self.public_id).count()
        return data

class Gamify(db.Model):
    __tablename__ = 'gamify'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    keys_earned = db.Column(db.Integer, nullable=True, default=0)
    level = db.Column(db.String(50), nullable=True, default=None)
    status = db.Column(db.String(50), default="PENDING")
    date_registered = db.Column(db.DateTime, default=dt.now())

    def to_dict(self):
        data = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        return data

class BonusWallet(db.Model):
    __tablename__ = 'bonuswallet'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    product = db.Column(db.String(100), nullable=True)
    balance = db.Column(db.Integer, nullable=True, default=0)
    status = db.Column(db.String(50), default="ACTIVE")
    date_registered = db.Column(db.DateTime, default=dt.now())
    transaction = relationship('WalletTransaction', backref='bonuswallet')

    def to_dict(self):
        data = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        return data

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    ref = db.Column(db.Text)
    desc = db.Column(db.Text)
    t_type = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    bal_bf = db.Column(db.Float, nullable=True)
    bal_af = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default="SUCCESS")
    remark = db.Column(db.Text, nullable=True)
    date_registered = db.Column(db.DateTime, default=dt.utcnow())
    date = db.Column(db.String(20), default=today)
    month = db.Column(db.String(20), default=month)
    year = db.Column(db.String(20), default=today_raw.year)

    # Convert object to dictionary, including related Programmes data
    def obj_to_dict(self):
        # Construct dictionary with Favourite fields
        transaction = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        return transaction

class WalletTransaction(db.Model):
    __tablename__ = 'wallettransaction'
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('bonuswallet.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    ref = db.Column(db.Text)
    desc = db.Column(db.Text)
    t_type = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    bal_bf = db.Column(db.Float, nullable=True)
    bal_af = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default="SUCCESS")
    remark = db.Column(db.Text, nullable=True)
    date_registered = db.Column(db.DateTime, default=dt.utcnow())
    date = db.Column(db.String(20), default=today)
    month = db.Column(db.String(20), default=month)
    year = db.Column(db.String(20), default=today_raw.year)

    # Convert object to dictionary, including related Programmes data
    def obj_to_dict(self):
        # Construct dictionary with Favourite fields
        transaction = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        return transaction

class SupportTicket(db.Model):
    __tablename__ = 'supportticket'
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String(50), nullable=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)
    status = db.Column(db.String(20), default='OPEN', nullable=False)
    priority = db.Column(db.String(20), default='MEDIUM', nullable=False)
    ticket_comment = relationship('TicketComment', backref='supportticket')

    def __init__(self, title, desc, std_id, advisor_id):
        self.title = title
        self.description = desc
        self.std_id = std_id
        self.assigned_to = advisor_id

    def __repr__(self):
        return f"<SupportTicket id={self.id} title={self.title} status={self.status} priority={self.priority}>"

    def obj_to_dict(self):
        # Construct dictionary with Favourite fields
        favourite_data = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        return favourite_data

    def comment(self):
        # Construct dictionary with Favourite fields
        favourite_data = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        favourite_data[ 'comments' ] = [ cc.obj_to_dict() for cc in self.ticket_comment ]
        favourite_data[ 'student' ] = Client.query.filter_by(id=self.std_id).first().obj_to_dict()
        return favourite_data

class TicketComment(db.Model):
    __tablename__ = 'ticketcomment'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('supportticket.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)

    def __init__(self, ticket_id, user_id, comment):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.comment = comment

    def __repr__(self):
        return f"<TicketComment id={self.id} ticket_id={self.ticket_id} user_id={self.user_id}>"

    def obj_to_dict(self):
        # Construct dictionary with Favourite fields
        favourite_data = { column.name: getattr(self, column.name) for column in self.__table__.columns }
        return favourite_data

