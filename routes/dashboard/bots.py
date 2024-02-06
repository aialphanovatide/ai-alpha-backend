from routes.news_bot.index import activate_news_bot
from flask import render_template, session as flask_session, redirect, url_for, jsonify, Blueprint
from config import Session as DBSession, Chart, CoinBot, Category




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



# Gets the last chart updated with Support and resistance lines - Return a DATE
@bots_route.route('/get_last_chart_update', methods=['GET'])
def get_last_chart_update():
    try:
        with DBSession() as db_session:
            last_update = (
                db_session.query(Chart, CoinBot.bot_name)
                .outerjoin(CoinBot, Chart.coin_bot_id == CoinBot.bot_id)
                .order_by(Chart.created_at.desc())
                .first()
            )

        if last_update:
            chart, bot_name = last_update
            formatted_date = chart.created_at.strftime('%m/%d/%Y %H:%M')

            return jsonify({
                'success': True,
                'last_update': {
                    'coin_bot_name': bot_name,
                    'formatted_date': formatted_date
                }
            })
        else:
            return jsonify({'success': False, 'message': 'there is no updates available'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


