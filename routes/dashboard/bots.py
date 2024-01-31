from config import Category
from routes.news_bot.index import activate_news_bot
from flask import render_template, session as flask_session
from flask import redirect, url_for
from config import Session as DBSession
from flask import Blueprint


bots_route = Blueprint('bots', __name__)

@bots_route.route('/bots')
def bots():
    if 'user' not in flask_session:
        return redirect(url_for('login'))

    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    for category in categories:
        print(category.category)
        activate_news_bot(category.category)

    any_inactive = any(not category.is_active for category in categories)

    return render_template('home/bots.html', admin=flask_session['user'], categories=categories, any_inactive=any_inactive)

