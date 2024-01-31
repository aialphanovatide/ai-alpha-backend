import os
from config import Admin, Analysis, AnalysisImage, Category, Chart, CoinBot, Keyword
#from routes.slack.templates.product_alert_notification import send_notification_to_product_alerts_slack_channel
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.trendspider.index import trendspider_notification_bp
from routes.tradingview.index import tradingview_bp
from routes.news_bot.index import activate_news_bot, deactivate_news_bot, scrapper_bp
from routes.telegram.index import telegram_bp 
from routes.slack.slack_actions import slack_events_bp
from flask_cors import CORS
from websocket.socket import socketio
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 
from flask import Blueprint


delete_kw = Blueprint('delete_keyword', __name__)



@delete_kw.route('/delete_keyword', methods=['POST'])
def delete_keyword():
    try:
        keyword_id = request.json.get('keyword_id')
        print('keyword_id', keyword_id)
        with DBSession() as db_session:
            keyword = db_session.query(Keyword).filter_by(keyword_id=keyword_id).first()
            print('keyword :', keyword)

            if keyword:
                db_session.delete(keyword)
                db_session.commit()
                return jsonify({'success': True, 'message': 'Keyword deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Keyword not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})