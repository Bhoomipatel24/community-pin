
from extension import db
from sqlalchemy import CheckConstraint



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text)
    name = db.Column(db.Text)
    password = db.Column(db.Text)
    role = db.Column(db.Text, CheckConstraint("role IN ('business', 'personal', 'admin')"))
    address = db.Column(db.Text)
    g_token = db.Column(db.Text)
    activation_status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class News(db.Model):
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    img = db.Column(db.Text)
    news_type = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    rejection_comment = db.Column(db.Text)
    creation_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # FK for checking getting individual user news
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))