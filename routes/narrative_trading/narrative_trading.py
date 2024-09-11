import datetime
from config import NarrativeTrading, Session, session, CoinBot
from flask import jsonify, Blueprint, request
from sqlalchemy import desc
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError
from utils.session_management import create_response
from sqlalchemy.exc import SQLAlchemyError
from services.openai.dalle import ImageGenerator
from services.aws.s3 import ImageProcessor

sched = BackgroundScheduler()
if sched.state != 1:
    sched.start()
    print("Scheduler started for Narrative Trading")

narrative_trading_bp = Blueprint('narrative_trading', __name__)

image_generator = ImageGenerator()
image_processor = ImageProcessor()


@narrative_trading_bp.route('/get_narrative_trading/<int:coin_bot_id>', methods=['GET'])
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
    session = Session()
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

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error="Internal server error occurred.")), 500

    finally:
        session.close()
        
        
        
def get_narrative_trading_by_id(coin_bot_id):
    return session.query(NarrativeTrading).filter_by(coin_bot_id=coin_bot_id).order_by(desc(NarrativeTrading.created_at)).all()

def get_narrative_trading_by_name(coin_bot_name):
    coin = session.query(CoinBot).filter(
        CoinBot.bot_name == coin_bot_name).first()
    return session.query(NarrativeTrading).filter_by(coin_bot_id=coin.bot_id).all() if coin else None

@narrative_trading_bp.route('/get_narrative_trading_by_coin', methods=['GET'])
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
    session = Session()
    try:
        coin_bot_name = request.args.get('coin_bot_name')
        coin_bot_id = request.args.get('coin_bot_id')

        if not coin_bot_id and not coin_bot_name:
            return jsonify(create_response(success=False, error='Coin ID or name is missing')), 400

        narrative_trading_objects = []
        if coin_bot_name:
            narrative_trading_objects = get_narrative_trading_by_name(coin_bot_name, session)
        elif coin_bot_id:
            narrative_trading_objects = get_narrative_trading_by_id(coin_bot_id, session)

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

        session.commit()
        return jsonify(create_response(success=True, data=narrative_trading_data)), 200

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error="Internal server error occurred.")), 500

    finally:
        session.close()

@narrative_trading_bp.route('/get_narrative_trading', methods=['GET'])
def get_all_narrative_trading():
    """
    Retrieve all narrative trading posts.

    Returns:
        JSON response:
            - 'message': List of narrative trading data
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    session = Session()
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

        session.commit()
        response = create_response(success=True, data=narrative_trading_data)
        return response, 200

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        response = create_response(success=False, error="Database error occurred.")
        return response, 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        response = create_response(success=False, error="Internal server error occurred.")
        return response, 500

    finally:
        session.close()


@narrative_trading_bp.route('/post_narrative_trading', methods=['POST'])
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
    session = Session()
    try:
        coin_bot_id = request.form.get('coinBot')
        content = request.form.get('content')
        category_name = request.form.get('category_name')

        if not (coin_bot_id and content):
            return jsonify(create_response(success=False, error='One or more required values are missing')), 400

        # Call the function to handle posting
        narrative_trading_post = publish_narrative_trading(coin_bot_id, content, category_name, session)
        
        if narrative_trading_post is None:
            return jsonify(create_response(success=False, error='Failed to publish narrative trading')), 500

        session.commit()
        return jsonify(create_response(success=True, data=narrative_trading_post, message='Narrative Trading posted successfully')), 201

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error="Internal server error occurred.")), 500

    finally:
        session.close()

    

@narrative_trading_bp.route('/delete_narrative_trading/<int:narrative_trading_id>', methods=['DELETE'])
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
    session = Session()
    try:
        narrative_trading_to_delete = session.query(NarrativeTrading).filter(
            NarrativeTrading.narrative_trading_id == narrative_trading_id).first()

        if not narrative_trading_to_delete:
            return jsonify(create_response(success=False, error='narrative_trading not found')), 404

        session.delete(narrative_trading_to_delete)
        session.commit()

        return jsonify(create_response(success=True, message='narrative_trading deleted successfully')), 200

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error="Internal server error occurred.")), 500

    finally:
        session.close()

@narrative_trading_bp.route('/edit_narrative_trading/<int:narrative_trading_id>', methods=['PUT'])
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
    session = Session()
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

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error="Internal server error occurred.")), 500

    finally:
        session.close()


@narrative_trading_bp.route('/get_last_narrative_trading', methods=['GET'])
def get_last_narrative_trading():
    """
    Retrieve information about the last narrative trading created.

    Returns:
        JSON response:
            - 'last_narrative_trading': Dictionary containing details of the last narrative trading
            - 'success': True if successful, False otherwise
            - 'status': HTTP status code
    """
    session = Session()
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
            'coin_name': coin.bot_name if coin else None,
            'category_name': last_narrative_trading.category_name,
            'created_at': last_narrative_trading.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify(create_response(success=True, data={'last_narrative_trading': narrative_trading_data})), 200

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify(create_response(success=False, error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        print(f"Internal server error: {str(e)}")
        return jsonify(create_response(success=False, error="Internal server error occurred.")), 500

    finally:
        session.close()

def publish_narrative_trading(coin_bot_id, content, category_name, session):
    """
    Publish a narrative trading post. Generate an image, upload it to S3, and then create the narrative trading post.

    Args:
        coin_bot_id (int): The ID of the coin bot
        content (str): The content of the narrative trading post
        category_name (str): The name of the category
        session (Session): The database session

    Returns:
        dict: The created NarrativeTrading object as a dictionary, or None if an error occurred
    """
    try:
        # Extract title and adjust content
        title_end_index = content.find('\n')
        if title_end_index != -1:
            title = content[:title_end_index].strip()
            content = content[title_end_index+1:]
        else:
            title = ""

        print(f"Title: {title}")

        # Generate and upload image
        image = image_generator.generate_image(content)
        if not image:
            raise ValueError("Image not generated")

       
        image_filename = f"{title}.jpg"
        resized_image_url = image_processor.process_and_upload_image(
            image_url=image,
            bucket_name='appnarrativetradingimages',
            image_filename=image_filename
        )
        if not resized_image_url:
            raise ValueError("Error resizing and uploading the image to S3")

        image_url = resized_image_url
        
        # Create and save the NarrativeTrading object
        new_narrative_trading = NarrativeTrading(
            narrative_trading=content,
            category_name=category_name,
            coin_bot_id=coin_bot_id,
            image=image_url
        )
        session.add(new_narrative_trading)
        session.commit()
        return create_response(success=True, 
                               data=new_narrative_trading.to_dict(), 
                               message='Narrative Trading posted successfully')

    except SQLAlchemyError as e:
        session.rollback()
        return create_response(success=False, error=f"Database error occurred: {str(e)}")

    except ValueError as e:
        session.rollback()
        return create_response(success=False, error=f"Value error occurred: {str(e)}")

    except Exception as e:
        session.rollback()
        return create_response(success=False, error=f"Internal server error occurred: {str(e)}")
    finally:
        session.close()


@narrative_trading_bp.route('/schedule_narrative_post', methods=['POST'])
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
        print(f"Error retrieving jobs: {str(e)}")
        return jsonify(create_response(success=False, error="Failed to retrieve jobs.")), 500

@narrative_trading_bp.route('/delete_scheduled_narrative_job/<string:job_id>', methods=['DELETE'])
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
        print(f"Job lookup error: {str(e)}")
        return jsonify(create_response(success=False, error="Job not found.")), 404

    except Exception as e:
        print(f"Error deleting job: {str(e)}")
        return jsonify(create_response(success=False, error="Failed to delete job.")), 500
    
