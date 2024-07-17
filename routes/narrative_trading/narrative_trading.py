import os
import boto3
import datetime
import requests
from PIL import Image
from io import BytesIO
from http import HTTPStatus
from sqlalchemy import desc
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from config import NarrativeTrading, session, CoinBot, Session
from routes.news_bot.poster_generator import generate_poster_prompt
from utils.session_management import handle_db_session, create_response
from services.aws.s3 import image as image_processor

sched = BackgroundScheduler()
if sched.state != 1:
    sched.start()
    print("--- Third Scheduler started ---")

narrative_trading_bp = Blueprint('narrative_trading', __name__)

load_dotenv()

AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')


@narrative_trading_bp.route('/get_narrative_trading/<int:coin_bot_id>', methods=['GET'])
@handle_db_session
def get_narrative_trading(coin_bot_id):
    """
    Retrieve narrative trading posts by coin bot ID.

    Args:
        coin_bot_id (int): ID of the coin bot

    Returns:
        JSON response:
            - Success: True if narrative trading posts are retrieved successfully
            - Error: Error message if any exception occurs
    """
    try:
        narrative_trading_objects = get_narrative_trading_by_id(coin_bot_id)
        if not narrative_trading_objects:
            return jsonify(create_response(success=False, error='No narrative trading found')), 404

        narrative_trading_data = []
        for nt in narrative_trading_objects:
            nt_dict = nt.to_dict()
            nt_dict.pop('narrative_trading_images', None)
            nt_dict.pop('image', None)
            nt_dict['category_name'] = nt.category_name
            nt_dict['coin_bot_id'] = nt.coin_bot_id 
            narrative_trading_data.append(nt_dict)

        return jsonify(create_response(success=True, data=narrative_trading_data)), 200

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


# Fn to get narrative_trading related to a coin id
def get_narrative_trading_by_id(coin_bot_id):
    return session.query(NarrativeTrading).filter_by(coin_bot_id=coin_bot_id).order_by(desc(NarrativeTrading.created_at)).all()

# Fn to get Narrative trading related to a coin name
def get_narrative_trading_by_name(coin_bot_name):
    coin = session.query(CoinBot).filter(
        CoinBot.bot_name == coin_bot_name).first()
    return session.query(NarrativeTrading).filter_by(coin_bot_id=coin.bot_id).all() if coin else None

# fn to get nt images
def get_narrative_trading_images(narrative_trading_object):
    return [{'image_id': img.image_id, 'image': img.image} for img in session.query(NarrativeTrading).filter_by(narrative_trading_id=narrative_trading_object.narrative_trading_id).all()]

@narrative_trading_bp.route('/api/get_narrative_trading_by_coin', methods=['GET'])
@handle_db_session
def get_narrative_trading_by_coin():
    """
    Retrieve narrative trading posts by coin bot name or ID.

    Args (query parameters):
        coin_bot_name (str): Name of the coin bot
        coin_bot_id (int): ID of the coin bot

    Returns:
        JSON response:
            - Success: True if narrative trading posts are retrieved successfully
            - Error: Error message if any exception occurs
    """
    try:
        coin_bot_name = request.args.get('coin_bot_name')
        coin_bot_id = request.args.get('coin_bot_id')

        if not coin_bot_id and not coin_bot_name:
            return jsonify(create_response(success=False, error='Coin ID or name is missing')), 400

        narrative_trading_objects = []
        if coin_bot_name:
            narrative_trading_objects = get_narrative_trading_by_name(coin_bot_name)
        elif coin_bot_id:
            narrative_trading_objects = get_narrative_trading_by_id(coin_bot_id)

        if not narrative_trading_objects:
            return jsonify(create_response(success=False, error='No narrative trading found')), 404

        narrative_trading_data = []
        for nt in narrative_trading_objects:
            nt_dict = nt.to_dict()
            nt_dict.pop('narrative_trading_images', None)
            nt_dict.pop('image', None)
            nt_dict['category_name'] = nt.category_name
            nt_dict['coin_bot_id'] = nt.coin_bot_id 
            narrative_trading_data.append(nt_dict)

        return jsonify(create_response(success=True, data=narrative_trading_data)), 200

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500

    
@narrative_trading_bp.route('/get_narrative_trading', methods=['GET'])
@handle_db_session
def get_all_narrative_trading():
    """
    Retrieve all narrative trading posts.

    Returns:
        JSON response:
            - 'message': List of narrative trading data
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        narrative_trading_objects = session.query(NarrativeTrading).order_by(
            desc(NarrativeTrading.created_at)).all()
        narrative_trading_data = []

        for analy in narrative_trading_objects:
            narrative_trading_dict = analy.to_dict()
            narrative_trading_dict.pop('narrative_trading_images', None)
            narrative_trading_dict.pop('image', None)
            narrative_trading_dict['category_name'] = analy.category_name
            narrative_trading_dict['coin_bot_id'] = analy.coin_bot_id
            narrative_trading_data.append(narrative_trading_dict)

        return jsonify(create_response(success=True, data=narrative_trading_data)), 200

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, error=str(e))), 500


@narrative_trading_bp.route('/post_narrative_trading', methods=['POST'])
@handle_db_session
def post_narrative_trading():
    """
    Create a new narrative trading post.

    Args (form parameters):
        coinBot (str): ID of the coin bot
        content (str): Content of the post
        category_name (str): Name of the category

    Returns:
        JSON response:
            - 'message': Success message
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        coin_bot_id = request.form.get('coinBot')
        content = request.form.get('content')
        category_name = request.form.get('category_name')

        if not (coin_bot_id and content):
            return jsonify(create_response(success=False, error='One or more required values are missing')), 400

        new_narrative_trading = NarrativeTrading(
            narrative_trading=content,
            coin_bot_id=coin_bot_id,
            category_name=category_name
        )
    

        session.add(new_narrative_trading)
        session.commit()
        
        
        image_processor = image_processor(aws_access_key=AWS_ACCESS, aws_secret_key=AWS_SECRET_KEY)

        if new_narrative_trading:
            image = generate_poster_prompt(new_narrative_trading.narrative_trading)
            print("image:", image)
            print("image generated")
            narrative_trading_id = new_narrative_trading.narrative_trading_id
            print('id narrative_trading', narrative_trading_id)
            image_filename = f"{narrative_trading_id}.jpg"    
            print('filename: ', image_filename)
            
            if image:
                try:
                    # Resize and upload the image to S3
                    resized_image_url = image_processor.process_and_upload_image(
                        image_url=image,
                        bucket_name='appnarrativetradingimages',
                        image_filename=image_filename
                    )

                    if resized_image_url:
                        print("Image resized and uploaded to S3 successfully.")
                    else:
                        print("Error resizing and uploading the image to S3.")
                except Exception as e:
                    print("Error:", e)
            else:
                print("Image not generated.")


            return jsonify(create_response(success=True, message='narrative_trading posted successfully')), 200

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, error=str(e))), 500
    

@narrative_trading_bp.route('/delete_narrative_trading/<int:narrative_trading_id>', methods=['DELETE'])
@handle_db_session
def delete_narrative_trading(narrative_trading_id):
    """
    Delete a narrative trading post by narrative_trading_id.

    Args:
        narrative_trading_id (int): ID of the narrative trading post to delete

    Returns:
        JSON response:
            - 'message': Success or error message
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        narrative_trading_to_delete = session.query(NarrativeTrading).filter(
            NarrativeTrading.narrative_trading_id == narrative_trading_id).first()

        if not narrative_trading_to_delete:
            return jsonify(create_response(success=False, error='narrative_trading not found')), 404

        session.delete(narrative_trading_to_delete)
        session.commit()

        return jsonify(create_response(success=True, message='narrative_trading deleted successfully')), 200

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, error=str(e))), 500

@narrative_trading_bp.route('/edit_narrative_trading/<int:narrative_trading_id>', methods=['PUT'])
@handle_db_session
def edit_narrative_trading(narrative_trading_id):
    """
    Edit an existing narrative trading post.

    Args:
        narrative_trading_id (int): ID of the narrative trading post to edit

    Returns:
        JSON response:
            - 'message': Success or error message
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        narrative_trading_to_edit = session.query(NarrativeTrading).filter(
            NarrativeTrading.narrative_trading_id == narrative_trading_id).first()

        if not narrative_trading_to_edit:
            return jsonify(create_response(success=False, error='narrative_trading not found')), 404

        new_content = request.json.get('content')

        if not new_content:
            return jsonify(create_response(success=False, error='New content is required to edit the narrative_trading')), 400

        narrative_trading_to_edit.narrative_trading = new_content
        session.commit()

        return jsonify(create_response(success=True, message='narrative_trading edited successfully')), 200

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, error=str(e))), 500


@narrative_trading_bp.route('/get_last_narrative_trading', methods=['GET'])
@handle_db_session
def get_last_narrative_trading():
    """
    Retrieve information about the last narrative trading created.

    Returns:
        JSON response:
            - 'last_narrative_trading': Dictionary containing details of the last narrative trading
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        last_narrative_trading = session.query(NarrativeTrading).order_by(
            NarrativeTrading.created_at.desc()).first()

        if not last_narrative_trading:
            return jsonify(create_response(success=False, error='No narrative_trading found')), 404

        coin = session.query(CoinBot).filter(
            CoinBot.bot_id == last_narrative_trading.coin_bot_id).first()

        narrative_trading_data = {
            'narrative_trading_id': last_narrative_trading.narrative_trading_id,
            'content': last_narrative_trading.narrative_trading,
            'coin_name': coin.bot_name,
            'category_name': last_narrative_trading.category_name,
            'created_at': last_narrative_trading.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify(create_response(success=True, data={'last_narrative_trading': narrative_trading_data})), 200

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, error=str(e))), 500



# Funtion to execute by the scheduler post
def publish_narrative_trading(coin_bot_id, content, category_name):
    title_end_index = content.find('\n')
    if title_end_index != -1:
        # Extract title and remove leading/trailing spaces
        title = content[:title_end_index].strip()
        # Extract content after the title
        content = content[title_end_index+1:]
    else:
        title = ''  # If no newline found, set title to empty string
    # Create new narrative_trading instance
    new_narrative_trading = NarrativeTrading(narrative_trading=content, category_name=category_name, coin_bot_id=coin_bot_id)
    session.add(new_narrative_trading)
    session.commit()
    print("Publishing narrative_trading with title:", title)

@narrative_trading_bp.route('/schedule_narrative_post', methods=['POST'])
@handle_db_session
def schedule_post():
    """
    Schedule a narrative trading post for future publishing.

    Args (form parameters):
        coinBot (str): ID of the coin bot
        category_name (str): Name of the category
        content (str): Content of the post
        scheduledDate (str): Scheduled date and time for publishing

    Returns:
        JSON response:
            - 'message': Success or error message
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        if not sched.running:
            sched.start()

        coin_bot_id = request.form.get('coinBot')
        category_name = request.form.get('category_name')
        content = request.form.get('content')
        scheduled_date_str = request.form.get('scheduledDate')

        if not (coin_bot_id and content and scheduled_date_str):
            return jsonify(create_response(success=False, error='One or more required values are missing')), 400

        scheduled_datetime = datetime.strptime(
            scheduled_date_str, '%a, %b %d, %Y, %I:%M:%S %p')

        sched.add_job(publish_narrative_trading, args=[coin_bot_id, content, category_name],
                      trigger=DateTrigger(run_date=scheduled_datetime))

        return jsonify(create_response(success=True, message='Post scheduled successfully')), 200

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500

@narrative_trading_bp.route('/get_narrative_trading_jobs', methods=['GET'])
@handle_db_session
def get_jobs():
    """
    Retrieve a list of all scheduled narrative trading jobs.

    Returns:
        JSON response:
            - 'jobs': List of dictionaries containing job details
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        job_listing = []
        for job in sched.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'args': str(job.args),
                'next_run_time': str(job.next_run_time) if hasattr(job, 'next_run_time') else None
            }
            job_listing.append(job_info)

        return jsonify(create_response(success=True, data={'jobs': job_listing})), 200

    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500


@narrative_trading_bp.route('/delete_scheduled_narrative_job/<string:job_id>', methods=['DELETE'])
@handle_db_session
def delete_scheduled_job(job_id):
    """
    Delete a scheduled narrative trading job by job ID.

    Args:
        job_id (str): ID of the job to delete

    Returns:
        JSON response:
            - 'message': Success or error message
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    try:
        job = sched.get_job(job_id)
        if not job:
            return jsonify(create_response(success=False, error='Scheduled job not found')), 404

        sched.remove_job(job_id)

        return jsonify(create_response(success=True, message='Scheduled job deleted successfully')), 200

    except JobLookupError as e:
        return jsonify(create_response(success=False, error=str(e))), 404
    except Exception as e:
        return jsonify(create_response(success=False, error=str(e))), 500

    

# ________________________ IMPROVED VERSION __________________________________

@narrative_trading_bp.route('/get_narrative_trading', methods=['GET'])
def get_narrative_trading():
    """
    Get narrative trading posts by coin bot name or ID.

    Query Parameters:
        coin_bot_name (str): The name of the coin bot
        coin_bot_id (int): The ID of the coin bot

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    session = Session()
    try:
        coin_bot_name = request.args.get('coin_bot_name')
        coin_bot_id = request.args.get('coin_bot_id')

        if not coin_bot_id and not coin_bot_name:
            return jsonify(create_response(success=False, error='Coin ID or name is missing')), HTTPStatus.BAD_REQUEST

        query = session.query(NarrativeTrading).join(CoinBot)

        if coin_bot_name:
            query = query.filter(CoinBot.bot_name == coin_bot_name)
        elif coin_bot_id:
            query = query.filter(CoinBot.bot_id == coin_bot_id)

        narrative_trading_objects = query.order_by(desc(NarrativeTrading.created_at)).all()

        if not narrative_trading_objects:
            return jsonify(create_response(success=False, error='No narrative trading found')), HTTPStatus.NOT_FOUND

        narrative_trading_data = [
            {
                **nt.to_dict(),
                'category_name': nt.category_name,
                'coin_bot_id': nt.coin_bot_id
            }
            for nt in narrative_trading_objects
        ]

        return jsonify(create_response(
            success=True,
            data=narrative_trading_data,
            message='Narrative trading data retrieved successfully'
        )), HTTPStatus.OK

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error=f"Database error: {str(e)}")), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error=f"Internal server error: {str(e)}")), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@narrative_trading_bp.route('/narrative_tradings', methods=['GET'])
def get_all_narrative_trading():
    """
    Get all narrative trading posts from all coins, ordered by creation date (descending).

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    session = Session()
    try:
        narrative_trading_objects = session.query(NarrativeTrading).order_by(
            desc(NarrativeTrading.created_at)).all()
        
        narrative_trading_data = []

        for nt in narrative_trading_objects:
            narrative_trading_dict = nt.to_dict()

            # Add coin bot id to the dictionary
            narrative_trading_dict['coin_bot_id'] = nt.coin_bot_id
            narrative_trading_dict['category_name'] = nt.category_name

            narrative_trading_data.append(narrative_trading_dict)

        response = create_response(
            success=True,
            data=narrative_trading_data,
            message='Narrative trading data retrieved successfully'
        )
        return jsonify(response), HTTPStatus.OK

    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Database error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        print(f"Internal server error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Internal server error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@narrative_trading_bp.route('/post_narrative_trading', methods=['POST'])
def post_narrative_trading():
    """
    Create a new narrative trading post and generate an associated image.

    Expected form data:
    - coinBot: ID of the coin bot
    - content: Content of the narrative trading
    - category_name: Name of the category

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    session = Session()
    try:
        coin_bot_id = request.form.get('coinBot')
        content = request.form.get('content')
        category_name = request.form.get('category_name')

        # Check if any of the required values is missing or null
        if not all([coin_bot_id, content, category_name]) or 'null' in [coin_bot_id, content, category_name]:
            response = create_response(
                success=False,
                error='One or more required values are missing or null'
            )
            return jsonify(response), HTTPStatus.BAD_REQUEST

        new_narrative_trading = NarrativeTrading(
            narrative_trading=content,
            coin_bot_id=coin_bot_id,
            category_name=category_name
        )
        
        session.add(new_narrative_trading)
        session.flush()  # This will assign an ID to new_narrative_trading
        
        # Generate and upload image
        image = generate_poster_prompt(new_narrative_trading.narrative_trading)
        if image:
            narrative_trading_id = new_narrative_trading.narrative_trading_id
            image_filename = f"{narrative_trading_id}.jpg"
            try:
                resized_image_url = image_processor.process_and_upload_image(image, 'appnarrativetradingimages', image_filename)
                if resized_image_url:
                    print("Image resized and uploaded to S3 successfully.")
                    new_narrative_trading.image_url = resized_image_url  # Assuming you have an image_url field
                else:
                    print("Error resizing and uploading the image to S3.")
            except Exception as e:
                print(f"Error in image processing: {str(e)}")
        else:
            print("Image not generated.")
            response = create_response(
            success=False,
            error=f"Image not generated"
            )
            return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR
            

        session.commit()

        response = create_response(
            success=True,
            message='Narrative trading posted successfully',
            data={'narrative_trading_id': new_narrative_trading.narrative_trading_id}
        )
        return jsonify(response), HTTPStatus.CREATED

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Database error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Internal server error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

#HERE
@narrative_trading_bp.route('/delete_narrative_trading/<int:narrative_trading_id>', methods=['DELETE'])
def delete_narrative_trading(narrative_trading_id):
    """
    Delete a narrative trading post and its associated image if it exists.

    Args:
        narrative_trading_id (int): The ID of the narrative trading to delete

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    session = Session()
    try:
        # Check if the narrative_trading_id exists
        narrative_trading_to_delete = session.query(NarrativeTrading).filter(
            NarrativeTrading.narrative_trading_id == narrative_trading_id).first()
        
        if narrative_trading_to_delete is None:
            response = create_response(
                success=False,
                error='Narrative trading not found'
            )
            return jsonify(response), HTTPStatus.NOT_FOUND

        # Delete the associated image if it exists
        # Note: This seems redundant as we're querying the same table again.
        # If there's a separate Image model, you should query that instead.
        narrative_trading_image_to_delete = session.query(NarrativeTrading).filter_by(narrative_trading_id=narrative_trading_id).first()

        if narrative_trading_image_to_delete:
            session.delete(narrative_trading_image_to_delete)

        # Delete the narrative_trading
        session.delete(narrative_trading_to_delete)
        session.commit()

        response = create_response(
            success=True,
            message='Narrative trading deleted successfully',
            data={'narrative_trading_id': narrative_trading_id}
        )
        return jsonify(response), HTTPStatus.OK

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Database error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        print(f"Internal server error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Internal server error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@narrative_trading_bp.route('/edit_narrative_trading/<int:narrative_trading_id>', methods=['PUT'])
def edit_narrative_trading(narrative_trading_id):
    """
    Edit a narrative trading post.

    Args:
        narrative_trading_id (int): The ID of the narrative trading to edit

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    session = Session()
    try:
        # Check if the narrative_trading_id exists
        narrative_trading_to_edit = session.query(NarrativeTrading).filter(
            NarrativeTrading.narrative_trading_id == narrative_trading_id).first()
        
        if narrative_trading_to_edit is None:
            response = create_response(
                success=False,
                error='Narrative trading not found'
            )
            return jsonify(response), HTTPStatus.NOT_FOUND

        # Update narrative_trading content if provided
        new_content = request.json.get('content')

        if not new_content:
            response = create_response(
                success=False,
                error='New content is required to edit the narrative trading'
            )
            return jsonify(response), HTTPStatus.BAD_REQUEST

        narrative_trading_to_edit.narrative_trading = new_content
        session.commit()

        response = create_response(
            success=True,
            message='Narrative trading edited successfully',
            data={'narrative_trading_id': narrative_trading_id}
        )
        return jsonify(response), HTTPStatus.OK

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Database error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Internal server error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@narrative_trading_bp.route('/get_last_narrative_trading', methods=['GET'])
def get_last_narrative_trading():
    """
    Get the name and date of the last narrative_trading created.

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    session = Session()
    try:
        # Retrieve the last narrative_trading created
        last_narrative_trading = session.query(NarrativeTrading).order_by(
            NarrativeTrading.created_at.desc()).first()

        if last_narrative_trading is None:
            response = create_response(
                success=False,
                error='No narrative_trading found'
            )
            return jsonify(response), HTTPStatus.NOT_FOUND

        coin = session.query(CoinBot).filter(
            CoinBot.bot_id == last_narrative_trading.coin_bot_id).first()

        # Extract relevant information
        narrative_trading_data = {
            'narrative_trading_id': last_narrative_trading.narrative_trading_id,
            'content': last_narrative_trading.narrative_trading,
            'coin_name': coin.bot_name if coin else 'Unknown',
            'category_name': last_narrative_trading.category_name,
            'created_at': last_narrative_trading.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        response = create_response(
            success=True,
            data={'last_narrative_trading': narrative_trading_data},
            message='Last narrative trading retrieved successfully'
        )
        return jsonify(response), HTTPStatus.OK

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Database error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        response = create_response(
            success=False,
            error=f"Internal server error: {str(e)}"
        )
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

def publish_narrative_trading(coin_bot_id, content, category_name):
    """
    Publish a narrative trading post.

    Args:
        coin_bot_id (int): ID of the coin bot
        content (str): Content of the post
        category_name (str): Name of the category

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    if not all([coin_bot_id, content, category_name]):
        response = create_response(success=False, error="Missing required arguments")
        return jsonify(response), HTTPStatus.BAD_REQUEST

    session = Session()
    try:
        title_end_index = content.find('\n')
        if title_end_index != -1:
            title = content[:title_end_index].strip()
            content = content[title_end_index+1:].strip()
        else:
            title = ""
            content = content.strip()

        new_narrative_trading = NarrativeTrading(
            narrative_trading=content,
            category_name=category_name,
            coin_bot_id=coin_bot_id,
            title=title,
            created_at=datetime.now()
        )
        session.add(new_narrative_trading)
        session.flush()  # This will assign an ID to new_narrative_trading
        session.commit()

        print(f"Published narrative trading: ID={new_narrative_trading.narrative_trading_id}, Title='{title}', CoinBot={coin_bot_id}")
        response = create_response(
            success=True,
            message="Narrative trading published successfully",
            data={"id": new_narrative_trading.narrative_trading_id}
        )
        return jsonify(response), HTTPStatus.OK

    except SQLAlchemyError as e:
        session.rollback()
        response = create_response(success=False, error=f"Database error: {str(e)}")
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        response = create_response(success=False, error=f"Internal server error: {str(e)}")
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

# @narrative_trading_bp.route('/schedule_narrative_post', methods=['POST'])
# def schedule_post():
#     """
#     Schedule a narrative trading post.

#     Expected form data:
#     - coinBot: ID of the coin bot
#     - category_name: Name of the category (optional)
#     - content: Content of the post
#     - scheduledDate: Date and time for the scheduled post (format: 'Mon, Jan 01, 2023, 12:00:00 AM')

#     Returns:
#         JSON response with status code:
#         - 200: Post scheduled successfully
#         - 400: Missing required values
#         - 500: Unexpected error
#     """
#     response = {"message": None, "error": None, "success": False}
#     status_code = 500  

#     try:
#         coin_bot_id = request.form.get('coinBot')
#         category_name = request.form.get('category_name')
#         content = request.form.get('content')
#         scheduled_date_str = request.form.get('scheduledDate')

#         # Validate required fields
#         if not all([coin_bot_id, content, scheduled_date_str]):
#             response["error"] = "One or more required values are missing"
#             response["status"] = 400
#             return jsonify(response), 400

#         # Parse the scheduled date
#         try:
#             scheduled_datetime = datetime.strptime(scheduled_date_str, '%a, %b %d, %Y, %I:%M:%S %p')
#         except ValueError:
#             response["error"] = "Invalid date format. Expected format: 'Mon, Jan 01, 2023, 12:00:00 AM'"
#             response["status"] = 400
#             return jsonify(response), 400

#         # Schedule the job
#         job = sched.add_job(
#             publish_narrative_trading,
#             args=[coin_bot_id, content, category_name],
#             trigger=DateTrigger(run_date=scheduled_datetime)
#         )

#         response["message"] = f"Post scheduled successfully. Job ID: {job.id}"
#         response["success"] = True
#         response["status"] = 200
#         status_code = 200

#     except Exception as e:
#         response["error"] = f"An unexpected error occurred: {str(e)}"
#         response["status"] = 500

#     return jsonify(response), status_code


# @narrative_trading_bp.route('/get_narrative_trading_jobs', methods=['GET'])
# def get_jobs():
#     """
#     Get all scheduled narrative trading jobs.

#     Returns:
#         JSON response with status code:
#         - 200: List of jobs retrieved successfully
#         - 500: Unexpected error
#     """
#     response = {"jobs": [], "message": None, "error": None, "success": False}
#     status_code = 500  # Default to server error

#     try:
#         for job in sched.get_jobs():
#             job_info = {
#                 'id': job.id,
#                 'name': job.name,
#                 'trigger': str(job.trigger),
#                 'args': str(job.args),
#                 'next_run_time': str(job.next_run_time) if job.next_run_time else None
#             }
#             response["jobs"].append(job_info)

#         response["message"] = "Jobs retrieved successfully"
#         response["success"] = True
#         response["status"] = 200
#         status_code = 200

#     except Exception as e:
#         response["error"] = f"An unexpected error occurred: {str(e)}"
#         response["status"] = 500

#     return jsonify(response), status_code


@narrative_trading_bp.route('/delete_scheduled_narrative_job/<string:job_id>', methods=['DELETE'])
def delete_scheduled_job(job_id):
    """
    Delete a scheduled job by job ID.

#     Args:
#         job_id (str): The ID of the job to delete

#     Returns:
#         JSON response with status code:
#         - 200: Job deleted successfully
#         - 404: Job not found
#         - 500: Unexpected error
#     """
#     response = {"message": None, "error": None, "success": False}
#     status_code = 500 

#     try:
#         # Find the scheduled job by ID
#         job = sched.get_job(job_id)
#         if job is None:
#             response["error"] = "Scheduled job not found"
#             response["status"] = 404
#             return jsonify(response), 404

#         # Delete the scheduled job
#         sched.remove_job(job_id)
#         response["message"] = "Scheduled job deleted successfully"
#         response["status"] = 200
#         response["success"] = True
#         status_code = 200

#     except JobLookupError as e:
#         response["error"] = str(e)
#         response["status"] = 404
#         status_code = 404
#     except Exception as e:
#         response["error"] = f"An unexpected error occurred: {str(e)}"
#         response["status"] = 500
#         status_code = 500

#     return jsonify(response), status_code
