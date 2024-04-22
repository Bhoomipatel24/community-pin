from flask import  render_template, redirect, url_for, session, current_app, flash
from datetime import datetime

from middlewares.middleware import check_and_refresh_token
from . import general_bp
import os
from werkzeug.utils import secure_filename

from models import News
from extension import db


@general_bp.route('/')
def home_page():
    return render_template('index.html', utc_date = datetime.utcnow())

@general_bp.route('/profile')
def profile():
    value = check_and_refresh_token()
    user_id = session.get('user_id')
    if value and user_id:
        mysql = current_app.mysql
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name, email, role, address FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        data = {
            'name': user[0],
            'email': user[1],
            'role': user[2],
            'address': user[3]
        }
        return render_template('general/profile.html', data = data)
    else:
        return redirect(url_for('auth_blueprint.login'))

@general_bp.route('/neighbourhood')
def news():
    value = check_and_refresh_token()
    if value:
        news = get_approved_news()
        return render_template('general/neighbourhood.html', news= news)
    else:
        return redirect(url_for('auth_blueprint.login'))
    
@general_bp.route('/news/<int:news_id>')
def news_detail(news_id):
    news_detail = True
    mysql = current_app.mysql
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, title, body, img, creation_date FROM news WHERE id = %s AND is_approved = 1", (news_id,))
    news_item = cursor.fetchone()
    cursor.close()
    if news_item:
        news_detail = {
            'id': news_item[0],
            'title': news_item[1],
            'body': news_item[2],
            'img': news_item[3],
            'creation_date': news_item[4]
        }
        return render_template('general/news_detail.html', news=news_detail)
    else:
        return render_template('general/error.html', error='Sorry that news is not available now.'), 404
    
from flask import request

@general_bp.route('/add-news', methods=['POST', 'GET'])
def add_news():
    if request.method == 'POST':
        news_title = request.form.get('news-title')
        news_body = request.form.get('news-body')
        news_image = request.files['news-image']
        news_type = request.form.get('news-type')
        user_id = session.get('user_id')
        filename = None
        if news_image:
            filename = secure_filename(news_image.filename)
            news_image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        news= News(title= news_title, body = news_body, img = filename, news_type = news_type, user_id = user_id)
        db.session.add(news)
        db.session.commit()
        flash('News successfully added. Please wait for admin approval to be listed', 'success')
        return redirect(url_for('general_bp.news'))  # Redirect to a success page or another route
    else:
        value = check_and_refresh_token()
        if value:
            return render_template('general/add-news.html')
        else:
            return redirect(url_for('auth_blueprint.login'))

@general_bp.route('/approve-news', methods=['GET', 'POST'])
def approve_news():
    if request.method == 'POST':
        news_id = request.form.get('news_id')
        value = request.form.get('value')
        news = News.query.get(news_id)
        if news_id:
            if value == 'reject':
                news.is_rejected = True
                news.is_approved = False
                news.rejection_comment = request.form.get('rejection_reason')
            elif value == 'approve':
                news.is_approved = True
            db.session.commit()
        else:
            flash('Invalid request. Please provide news ID.', 'error')

    value = check_and_refresh_token()
    if value:
        is_admin = check_is_admin(session['user_id'])
        if is_admin:
            mysql = current_app.mysql
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id, title, body FROM news WHERE is_approved = 0 and is_rejected = 0 ORDER BY creation_date DESC LIMIT 9")
            news = cursor.fetchall()
            cursor.close()
            news_dict_list = []
            for news_item in news:
                news_dict = {
                    'id': news_item[0],
                    'title': news_item[1],
                    'body': news_item[2],
                }
                news_dict_list.append(news_dict)
            return render_template('general/approve-news.html', news=news_dict_list)
        else:
            return redirect(url_for('general_bp.home_page')) 
    else:
        return redirect(url_for('auth_blueprint.login'))

@general_bp.route('/notifications', methods=['GET'])
def notifications():
    value = check_and_refresh_token()
    if value:
        news = News.query.filter_by(user_id=session.get('user_id')).order_by(News.creation_date.desc()).limit(20).all()
        news_dict_list = []
        for news_item in news:
            rejection_comment = None
            news_approval_status = 'pending'
            if news_item.is_approved == 1 and news_item.is_rejected == 0:
                news_approval_status = 'approved'
            if news_item.is_approved == 0 and news_item.is_rejected == 1:
                news_approval_status = 'rejected'
            news_dict= {
                'title': news_item.title,
                'news_approval_status': news_approval_status,
                'rejection_comment': news_item.rejection_comment
            }
            news_dict_list.append(news_dict)
        return render_template('general/notifications.html', news= news_dict_list)
    else:
        return redirect(url_for('auth_blueprint.login'))
    

def check_is_admin(user_id):
    mysql = current_app.mysql
    cursor = mysql.connection.cursor()
    query = f'select role from users where id = {user_id}'
    cursor.execute(query)
    role = cursor.fetchone()
    if role[0] == 'admin':
        return True
    else:
        return False

def get_approved_news():
    approved_news = News.query.filter_by(is_approved=True).order_by(News.creation_date.desc()).limit(9).all()
    news_dict_list = []
    for news_item in approved_news:
        news_dict = {
            'id': news_item.id,
            'title': news_item.title,
            'body': news_item.body,
            'img': news_item.img,
            'creation_date': news_item.creation_date
        }
        news_dict_list.append(news_dict)
    return news_dict_list