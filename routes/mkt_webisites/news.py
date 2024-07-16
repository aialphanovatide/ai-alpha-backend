
from config import session, Article, Session
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from http import HTTPStatus
from datetime import datetime, timedelta
from sqlalchemy import desc

website_news_bp = Blueprint('mtkWebsiteNews', __name__)

# @website_news_bp.route('/api/get/latest_news', methods=['GET'])
# def get_latest_news():
#     try:
#         coin_bot_id = request.args.get('coin_bot_id')

#         if coin_bot_id is None:
#             return {'error': 'Coin Bot ID is required'}, 400

#         try:
#             coin_bot_id = int(coin_bot_id)
#         except ValueError:
#             return {'error': 'Invalid Coin Bot ID'}, 400

#         limit = request.args.get('limit')
#         if limit is not None:
#             try:
#                 limit = int(limit)
#             except ValueError:
#                 return {'error': 'Invalid limit parameter'}, 400
#         else:
#             limit = 20 

#         start_date = datetime.now() - timedelta(days=30)

#         # Utilizar el límite en la consulta
#         articles = session.query(Article).filter(
#             Article.coin_bot_id == coin_bot_id,
#             Article.created_at >= start_date
#         ).order_by(desc(Article.created_at)).limit(limit).all()

#         if articles:
#             articles_list = []

#             for article in articles:
#                 article_dict = {
#                     'article_id': article.article_id,
#                     'date': article.date,
#                     'title': article.title,
#                     'url': article.url,
#                     'summary': article.summary,
#                     'created_at': article.created_at.isoformat(),
#                     'coin_bot_id': article.coin_bot_id,
#                     'images': []
#                 }


#                 articles_list.append(article_dict)

#             return {'articles': articles_list}, 200
#         else:
#             return {'message': f'No articles found for Coin Bot {coin_bot_id} in the last day'}, 204
 
#     except Exception as e:
#         return {'error': f'An error occurred while fetching the latest news: {str(e)}'}, 500

# @website_news_bp.route('/api/get/article', methods=['GET'])
# def get_article_by_id():
#     try:
#         article_id = request.args.get('article_id')

#         if article_id is None:
#             return {'error': 'Article ID is required'}, 400

#         try:
#             article_id = int(article_id)
#         except ValueError:
#             return {'error': 'Invalid Article ID'}, 400

#         article = session.query(Article).filter(Article.article_id == article_id).first()

#         if article:
#             article_data = {
#                 'article_id': article.article_id,
#                 'date': article.date,
#                 'title': article.title,
#                 'url': article.url,
#                 'summary': article.summary,
#                 'created_at': article.created_at.isoformat(),
#                 'coin_bot_id': article.coin_bot_id,
#                 'images': []
#             }


#             return {'article': article_data}, 200
#         else:
#             return {'message': f'Article with ID {article_id} not found'}, 404

#     except Exception as e:
#         return {'error': f'An error occurred while fetching the article: {str(e)}'}, 500
    

# _____________________ IMPROVED VERSION __________________________________________________


@website_news_bp.route('/api/get/latest_news', methods=['GET'])
def get_latest_news():
    """
    Retrieve the latest news articles for a specific coin bot.

    Args:
        coin_bot_id (int): The ID of the coin bot.
        limit (int, optional): The maximum number of articles to return. Defaults to 20.

    Returns:
        JSON: A list of articles or an error message.
    """
    response = {
        "data": None,
        "error": None,
        "status": HTTPStatus.OK
    }

    session = Session()

    try:
        coin_bot_id = request.args.get('coin_bot_id', type=int)
        limit = request.args.get('limit', 20, type=int)

        if coin_bot_id is None:
            response["error"] = "Coin Bot ID is required"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        start_date = datetime.now() - timedelta(days=30)

        articles = session.query(Article).filter(
            Article.coin_bot_id == coin_bot_id,
            Article.created_at >= start_date
        ).order_by(desc(Article.created_at)).limit(limit).all()

        if articles:
            articles_list = []
            for article in articles:
                article_dict = article.as_dict()
                article_dict['created_at'] = article_dict['created_at'].isoformat()
                article_dict['updated_at'] = article_dict['updated_at'].isoformat()
                articles_list.append(article_dict)
            
            response["data"] = articles_list
        else:
            response["error"] = f"No articles found for Coin Bot {coin_bot_id} in the last 30 days"
            response["status"] = HTTPStatus.NOT_FOUND

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

    return jsonify(response), response["status"]

@website_news_bp.route('/api/get/article', methods=['GET'])
def get_article_by_id():
    """
    Retrieve a specific article by its ID.

    Args:
        article_id (int): The ID of the article to retrieve.

    Returns:
        JSON: The article data or an error message.
    """
    response = {
        "data": None,
        "error": None,
        "status": HTTPStatus.OK
    }

    session = Session()

    try:
        article_id = request.args.get('article_id', type=int)

        if article_id is None:
            response["error"] = "Article ID is required"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        article = session.query(Article).filter(Article.article_id == article_id).first()

        if article:
            article_data = article.as_dict()
            article_data['created_at'] = article_data['created_at'].isoformat()
            article_data['updated_at'] = article_data['updated_at'].isoformat()
            response["data"] = article_data
        else:
            response["error"] = f"Article with ID {article_id} not found"
            response["status"] = HTTPStatus.NOT_FOUND

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

    return jsonify(response), response["status"]
