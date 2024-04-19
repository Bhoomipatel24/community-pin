import os

from flask import Flask, redirect, url_for, session
from flask_jwt_extended import (JWTManager,
                                create_access_token,
                                create_refresh_token,
                                set_access_cookies,
                                set_refresh_cookies,
                            )
from authlib.integrations.flask_client import OAuth
from flask_mysqldb import MySQL
from datetime import timedelta

import config

# extension
from extension import db

# Blueprints
from general import general_bp
from auth import auth_blueprint


app = Flask(__name__)

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

# SqlAlchamy
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}"

app.secret_key = config.SECRET_KEY

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['JWT_SECRET_KEY'] = 'super-secret' 
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=10) 
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)


jwt = JWTManager(app)
mysql = MySQL(app)
oauth = OAuth(app)
db.init_app(app)

app.register_blueprint(general_bp)
app.register_blueprint(auth_blueprint)

oauth.register(
    "myApp",
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email",},
    server_metadata_url=config.OAUTH_META_URL,
    )

def check_login_status():
    return session.get('user')


@app.route("/google-login")
def google_login():
    return oauth.myApp.authorize_redirect(redirect_uri=url_for('google_call_back', _external = True))



@app.route("/google-redirect")
def google_call_back():
    token = oauth.myApp.authorize_access_token()
    sub = token['userinfo']['sub']
    email = token['userinfo']['email']
    name = token['userinfo']['given_name']+' '+token['userinfo']['family_name']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, g_token FROM users WHERE g_token = %s", (sub,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (g_token, name) VALUES (%s, %s)", (sub, name))
        mysql.connection.commit()
    cursor.execute("SELECT id, g_token FROM users WHERE g_token = %s", (sub,))
    user = cursor.fetchone()
    cursor.close()
    data = {
            'id': user[0],
            'email': None,
            'g_token' : user[1]
            }
    access_token = create_access_token(identity=data)
    refresh_token= create_refresh_token(identity=data)
    resp = redirect(url_for('general_bp.profile'))
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    session['user'] = 'active'
    session['user_id']= user[0]
    return resp


@app.context_processor
def inject_logged_in():
    logged_in = check_login_status()
    return dict(logged_in=logged_in)

app.mysql = mysql


