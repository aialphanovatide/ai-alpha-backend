from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from config import CoinBot, PurchasedPlan, User, session, Category, Article, TopStory, TopStoryImage
from routes.news_bot.scrapper import start_periodic_scraping
from apscheduler.jobstores.base import JobLookupError
from flask import request, Blueprint, jsonify
from datetime import datetime, timedelta
from scheduler import scheduler
from sqlalchemy import exists
from sqlalchemy import desc
from sqlalchemy import exc

scrapper_bp = Blueprint(
    'scrapper_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


# Gets all top stories 
@scrapper_bp.route('/api/get/allTopStories', methods=['GET'])
def get_all_top_stories():
    try:
        top_stories_list = []
        top_stories = session.query(TopStory).order_by(desc(TopStory.created_at)).all()

        if not top_stories:
            return jsonify({'top_stories': 'No top stories found'}), 204
        else:
            for top_story in top_stories:
                top_story_dict = {
                    'top_story_id': top_story.top_story_id,
                    'story_date': top_story.story_date,
                    'summary': top_story.summary,
                    'created_at': top_story.created_at.isoformat(),
                    'coin_bot_id': top_story.coin_bot_id,
                    'images': []
                }

                for image in top_story.images:
                     top_story_dict['images'].append({
                         'image_id': image.image_id,
                         'image': image.image,
                         'created_at': image.created_at.isoformat(),
                         'top_story_id': image.top_story_id
                     })

                top_stories_list.append(top_story_dict)

        
            return jsonify({'top_stories': top_stories_list}), 200
           
    except Exception as e:
        return jsonify({'error': f'An error occurred getting the top stories: {str(e)}'}), 500

# Delete a top stories 
@scrapper_bp.route('/api/delete/top-story/<int:top_story_id>', methods=['DELETE'])
def delete_top_story(top_story_id):
    try:
        top_story = session.query(TopStory).filter(TopStory.top_story_id == top_story_id).first()

        if not top_story:
            return jsonify({'message': 'No top story found'}), 404
        
        top_story_image = session.query(TopStoryImage).filter(TopStoryImage.top_story_id==top_story.top_story_id).first()

        top_story_image = session.query(TopStoryImage).filter(TopStoryImage.top_story_id==top_story.top_story_id).first()

        # Delete the top story
        session.delete(top_story)
        session.delete(top_story_image)
        session.commit()

        return jsonify({'message': 'Top story deleted'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': f'An error occurred deleting the top story: {str(e)}'}), 500
    

def get_news(bot_name, time_range, limit):
    try:
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).first()

        if not coin_bot:
            return {'error': f'Coin {bot_name} not found'}, 404

        coin_bot_id = coin_bot.bot_id
        articles = None

        if time_range == 'today':
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'this week':
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'last month':
            today = datetime.now()
            start_date = today - timedelta(days=(today.weekday() + 30))
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = None

        # Ahora incluimos el límite en la consulta
        if start_date:
            articles = session.query(Article).filter(Article.coin_bot_id == coin_bot_id, Article.created_at >= start_date).order_by(desc(Article.created_at)).limit(limit).all()
        else:
            articles = session.query(Article).filter(Article.coin_bot_id == coin_bot_id).order_by(desc(Article.created_at)).limit(limit).all()


        if articles:
            articles_list = []

            for article in articles:
                article_dict = {
                    'article_id': article.article_id,
                    'date': article.date,
                    'title': article.title,
                    'url': article.url,
                    'summary': article.summary,
                    'created_at': article.created_at.isoformat(),
                    'coin_bot_id': article.coin_bot_id,
                    'images': []
                }

                # Include image information
                for image in article.images:
                    article_dict['images'].append({
                        'image_id': image.image_id,
                        'image': image.image,
                        'created_at': image.created_at.isoformat(),
                        'article_id': image.article_id
                    })

                articles_list.append(article_dict)

            return {'articles': articles_list}, 200
        else:
            return {'message': f'No articles found for {bot_name}'}, 204
 
    except Exception as e:
        return {'error': f'An error occurred getting the news for {bot_name}: {str(e)}'}, 500

@scrapper_bp.route('/api/get/news', methods=['GET'])
def get_news_by_bot_name():
    try:
        coin = request.args.get('coin')
        time_range = request.args.get('time_range')
        limit = request.args.get('limit', default=10, type=int)

        if time_range and time_range not in ["today", "this week", "last month"]:
            return {'error': "Time range isn't valid"}, 400

        if not coin:
            return {'error': 'Coin is required'}, 400
        else:
            res, status = get_news(bot_name=coin, time_range=time_range, limit=limit)
            return res, status
    except Exception as e:
        return {'error': f'An error occurred getting the news: {str(e)}'}, 500

@scrapper_bp.route('/get_categories', methods=['GET'])
def get_categories():
    """
    Retrieve all categories and their associated coin bots, sorted alphabetically.

    This endpoint fetches all categories (excluding 'hacks') from the database,
    orders them alphabetically by category name, and includes their associated
    coin bots (also sorted alphabetically by bot name).

    Returns:
        tuple: A tuple containing:
            - dict: A dictionary with a 'categories' key, whose value is a list of
                    category dictionaries. Each category dictionary contains:
                    - category_id (int): The unique identifier for the category
                    - category (str): The category slug
                    - category_name (str): The display name of the category
                    - time_interval (str): The time interval associated with the category
                    - is_active (bool): Whether the category is active
                    - icon (str): The icon associated with the category
                    - borderColor (str): The border color for the category
                    - created_at (datetime): The creation timestamp of the category
                    - coin_bots (list): A list of dictionaries, each representing a coin bot
                                        associated with the category. Each coin bot dictionary contains:
                                        - bot_id (int): The unique identifier for the bot
                                        - bot_name (str): The name of the bot
                                        - image (str): The image associated with the bot
                                        - created_at (datetime): The creation timestamp of the bot
            - int: HTTP status code (200 for success, 500 for error)

    Raises:
        Exception: If there's an error retrieving the categories from the database.

    Note:
        - Categories are sorted alphabetically by category_name.
        - Coin bots within each category are sorted alphabetically by bot_name.
        - The 'hacks' category is excluded from the results.
    """
    try:
        categories = session.query(Category).filter(Category.category != 'hacks').order_by(Category.category_name).all()
        category_data = []

        for category in categories:
            category_data.append({
                'category_id': category.category_id,
                'alias': category.alias,
                'name': category.name,
                'time_interval': category.time_interval,
                'is_active': category.is_active,
                'icon': category.icon,
                'borderColor': category.border_color,
                'created_at': category.created_at,
                'coin_bots': [{
                    'bot_id': bot.bot_id,
                    'bot_name': bot.bot_name,
                    'image': bot.image,
                    'created_at': bot.created_at
                } for bot in sorted(category.coin_bot, key=lambda x: x.bot_name)]
            })
        
        return {'categories': category_data}, 200

    except Exception as e:
        return {'Error': f'Error getting the categories: {str(e)}'}, 500

def activate_news_bot(category_name):
    try:
        if not scheduler.state:
            print('Scheduler not active')
            return 'Scheduler not active', 500
        
        category = session.query(Category).filter(Category.category == category_name.casefold()).first()
        
        if not category:
            print(f'{category_name.capitalize()} does not match any in the database')
            return f'{category_name.capitalize()} does not match any in the database', 404
        
        time_interval = category.time_interval
        category.is_active = True
        session.commit()
            
        job = scheduler.add_job(start_periodic_scraping, 'interval', minutes=time_interval, id=category_name, replace_existing=True, args=[category_name], max_instances=2)
        if job:
            print(f'{category_name.capitalize()} activated successfully')
        
        message = f'{category_name.capitalize()} activated successfully'
        # send_notification_to_product_alerts_slack_channel(title_message=message, sub_title='Message', message=f'An interval of *{time_interval} Minutes* has been set for scrapping data')
        return f'{category_name.capitalize()} News Bot activated', 200

    except Exception as e:
        print(f'Error while activating the {category_name.capitalize()} News Bot: {str(e)}')
        return f'Error while activating the {category_name.capitalize()} News Bot', 500


def deactivate_news_bot(category_name):

    try:
        category = session.query(Category).filter(Category.category == category_name).first()

        if not category:
            print(f'{category_name.capitalize()} does not match any in the database')
            return f'{category_name.capitalize()} does not match any in the database', 404


        scheduler.remove_job(category_name)
        category.is_active = False
        session.commit()

        message = f'{category_name.capitalize()} deactivated successfully'
        # send_notification_to_product_alerts_slack_channel(title_message=message, sub_title='Status', message='Inactive')
        return f'{category_name.capitalize()} deactivated', 200
    
    except JobLookupError as e:
        print(f'{category_name.capitalize()} News Bot not found: {str(e)}')
        return f'{category_name.capitalize()} News Bot not found: {str(e)}', 500

    except Exception as e:
        print(f'Error while deactivating {category_name.capitalize()}: {str(e)}')
        return f'Error while deactivating {category_name.capitalize()}: {str(e)}', 500


# Activates or desactivates a category: ex Layer 0  
@scrapper_bp.route('/api/news/bot', methods=['POST'])
def news_bot_commands():
        
        try:
            data = request.json
            command = data['command']
            category = data['category']
            category = str(category).casefold()

            if command == 'activate': 
                res, status = start_periodic_scraping(category)
                #res, status = activate_news_bot(category)
                return res, status
            elif command == 'deactivate':
                response, status = deactivate_news_bot(category)
                return response, status
            else:
                return 'Command not valid', 400
        except Exception as e:
            print(f'An error occurred: {str(e)}')
            return f'An error occurred: {str(e)}'
        


    #  initial_time = time.time()
    #             res, status = activate_news_bot(category)
    #             # res, status = start_periodic_scraping(category)
    #             final_time = time.time()
    #             final_scrapping_time = final_time - initial_time
    #             minutes, seconds = divmod(final_scrapping_time, 60)
    #             print(f"Final time: {minutes:.0f} minutes and {seconds:.2f} seconds")
    #             return res, status
        

@scrapper_bp.route('/check-email', methods=['GET'])
def check_email():
    """
    Check if a user with the given email exists and has a plan with 'founders' in reference_name.

    Args:
        email (str): Email address of the user to check.

    Response:
        200: User and plan found successfully.
        400: Missing required email parameter.
        404: User or plan not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None, 'data': None}
    try:
        email = request.args.get('email')

        email = email.replace("!verify ", "")
        if not email:
            response['message'] = 'Email parameter is required'
            return jsonify(response), 400

        user = session.query(User).filter_by(email=email).first()
        if not user:
            response['message'] = 'User not found'
            return jsonify(response), 404
        plan_exists = session.query(PurchasedPlan).filter(
            PurchasedPlan.user_id == user.user_id,
            PurchasedPlan.reference_name.ilike('%founders%')
        ).first()
        
        if plan_exists:
            print("plan", plan_exists)
            response['success'] = True
            response['message'] = 'User and plan found successfully'
            response['data'] = {
                "user_id": user.user_id,
                "nickname": user.nickname,
                "email": user.email,
                "email_verified": user.email_verified,
                "picture": user.picture,
                "auth0id": user.auth0id,
                "provider": user.provider,
                "created_at": user.created_at
            }
            return jsonify(response), 200
        else:
            response['message'] = "No plan with 'founders' found"
            return jsonify(response), 404

    except exc.SQLAlchemyError as e:
        session.rollback()
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500
