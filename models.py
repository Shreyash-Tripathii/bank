from flask_app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.username == user_id).first()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        if bcrypt.check_password_hash(self.password_hash, password):
            return True
        return False

    def get_id(self):
        return self.username

class Profile(db.Model):
    __tablename__ = "profile"
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(128))
    last = db.Column(db.String(128))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(7))
    pano = db.Column(db.String(12))
    address = db.Column(db.Text)
    phone = db.Column(db.BigInteger)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=user_id)
    userType = db.Column(db.String(10))

class Accounts(db.Model):
    __tablename__ = "accounts"
    id=db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=user_id)
    accno = db.Column(db.BigInteger, unique=True, nullable=False)
    trpin = db.Column(db.Integer)
    balance = db.Column(db.Float, default=0.0)
    visual = db.Column(db.String(6))

class DepWithID(db.Model):
    __tablename__ = "withdepid"
    id=db.Column(db.Integer, primary_key=True)
    accno=db.Column(db.BigInteger, nullable=False)
    trid=db.Column(db.String(10))
    amt=db.Column(db.Float)
    tran_type=db.Column(db.String(10))
    approve=db.Column(db.String(10))
    posted = db.Column(db.DateTime, default=datetime.now)

class Transfers(db.Model):
    __tablename__ = "transfers"
    id=db.Column(db.Integer, primary_key=True)
    from_acc=db.Column(db.BigInteger, nullable=False)
    to_acc=db.Column(db.BigInteger, nullable=False)
    amt=db.Column(db.Float)
    posted = db.Column(db.DateTime, default=datetime.now)


