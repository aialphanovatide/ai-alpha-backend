import datetime
import re
from sqlalchemy.orm import Session
from flask import Blueprint, jsonify, request
from config import Blacklist, CoinBot, Keyword, Site, Category
from config import Session as DBSession 

getBots = Blueprint('getAllBots', __name__)

@getBots.route('/get_all_bots', methods=['GET'])
def get_bots():
    try:
        with Session() as db_session:
            categories = db_session.query(Category).order_by(Category.category_id).all()
        
        bots = [{'category': category.category, 'isActive': category.is_active, 
                 'alias': category.category_name, 'icon': category.icon, 
                 'updated_at': category.updated_at, 'color': category.border_color} 
                for category in categories]
        return jsonify({'success': True, 'bots': bots}), 200
    except Exception as e:
        return jsonify({'success': False, 'bots': [], 'error': str(e)}), 500

@getBots.route('/create_coin_bot', methods=['POST'])
async def create_coin_bot():
    response = {'data': None, 'error': None, 'success': False}
    try:
        data = request.json
        current_time = datetime.datetime.now()

        # Required inputs
        required_fields = ['bot_name', 'category_id', 'url', 'keywords', 'blacklist']
        for field in required_fields:
            if field not in data:
                response['error'] = f'Missing field in request data: {field}'
                return jsonify(response), 400

        category_id = data['category_id']
        
        # Verify existing bot
        with DBSession() as db_session:
            existing_bot = db_session.query(CoinBot).filter_by(bot_name=data['bot_name']).first()
            if existing_bot:
                response['error'] = f"A bot with the name '{data['bot_name']}' already exists"
                return jsonify(response), 400

            # Verify if the category exists
            existing_category = db_session.query(Category).filter_by(category_id=category_id).first()
            if not existing_category:
                response['error'] = 'Category ID not found'
                return jsonify(response), 404

            # Create new bot
            new_bot = CoinBot(
                bot_name=data['bot_name'],
                category_id=category_id,
                created_at=current_time
            )
            with DBSession() as db_session:
                db_session.add(new_bot)
                db_session.commit()

            db_session.commit()

            # Create new Site
            url = data['url']
            site_name_match = re.search(r"https://www\.([^.]+)\.com", url)
            site_name = 'Unknown Site'
            if site_name_match:
                site_name = site_name_match.group(1)

            new_site = Site(
                site_name=site_name,
                data_source_url=url,
                coin_bot_id=new_bot.bot_id,
                created_at=current_time
            )
            with DBSession() as db_session:
                db_session.add(new_site)
                db_session.commit()

            # Add keywords to the bot
            keywords = [keyword.strip() for keyword in data['keywords'].split(',')]
            for keyword in keywords:
                new_keyword = Keyword(
                    word=keyword,
                    coin_bot_id=new_bot.bot_id,
                    created_at=current_time
                )
                with DBSession() as db_session:
                    db_session.add(new_keyword)

            # Add words to the bot Blacklist
            blacklist = [word.strip() for word in data['blacklist'].split(',')]
            for word in blacklist:
                new_blacklist_entry = Blacklist(
                    word=word,
                    coin_bot_id=new_bot.bot_id,
                    created_at=current_time
                )
                with DBSession() as db_session:
                    db_session.add(new_blacklist_entry)
                    db_session.commit()

            

        response['message'] = 'CoinBot created successfully'
        response['data'] = {
            'bot_id': new_bot.bot_id,
            'bot_name': new_bot.bot_name,
            'category_id': new_bot.category_id,
            'created_at': new_bot.created_at
        }
        response['success'] = True
        return jsonify(response), 200

    except Exception as e:
        response['error'] = f"Error creating CoinBot: {str(e)}"
        return jsonify(response), 500
