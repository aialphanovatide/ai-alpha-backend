
from config import session, Article
from flask import Blueprint, request
from datetime import datetime, timedelta
from sqlalchemy import desc

website_news_bp = Blueprint('mtkWebsiteNews', __name__)

@website_news_bp.route('/api/get/latest_news', methods=['GET'])
def get_latest_news():
    try:
        coin_bot_id = request.args.get('coin_bot_id')

        if coin_bot_id is None:
            return {'error': 'Coin Bot ID is required'}, 400

        try:
            coin_bot_id = int(coin_bot_id)
        except ValueError:
            return {'error': 'Invalid Coin Bot ID'}, 400

        start_date = datetime.now() - timedelta(days=1)

        articles = session.query(Article).filter(
            Article.coin_bot_id == coin_bot_id,
            Article.created_at >= start_date
        ).order_by(desc(Article.created_at)).all()

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
            return {'message': f'No articles found for Coin Bot {coin_bot_id} in the last day'}, 204
 
    except Exception as e:
        return {'error': f'An error occurred while fetching the latest news: {str(e)}'}, 500
