import datetime
from config import NarrativeTrading, Session, CoinBot
from flask import jsonify, Blueprint, request
from sqlalchemy import desc
from datetime import datetime
from sqlalchemy.orm import joinedload
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError
from utils.session_management import create_response
from sqlalchemy.exc import SQLAlchemyError
from services.openai.dalle import ImageGenerator
from services.aws.s3 import ImageProcessor
from routes.narrative_trading.nt_scheduler import sched
from redis_client.redis_client import cache_with_redis, update_cache_with_redis

narrative_trading_bp = Blueprint('narrative_trading', __name__)

image_generator = ImageGenerator()
image_processor = ImageProcessor()

@narrative_trading_bp.route('/narrative-trading', methods=['GET'])
@cache_with_redis()
def get_narrative_trading():
    """
    Retrieve narrative trading entries for a specific coin, with pagination.

    Query Parameters:
    - coin_id (int, optional): ID of the coin
    - coin_name (str, optional): Name of the coin
    - page (int, optional): Page number (default: 1)
    - limit (int, optional): Items per page (default: 10, max: 100)

    Returns:
    JSON with narrative trading data, total count, and pagination info.
    """
    session = Session()
    try:
        coin_id = request.args.get('coin_id', type=int)
        coin_name = request.args.get('coin_name')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Cap at 100

        if not coin_id and not coin_name:
            return jsonify(create_response(success=False, error='Coin ID or name is required')), 400

        query = session.query(NarrativeTrading).options(joinedload(NarrativeTrading.coin_bot))

        if coin_name:
            coin = session.query(CoinBot).filter(CoinBot.name == coin_name).first()
            if not coin:
                return jsonify(create_response(success=False, error='Coin not found')), 404
            query = query.filter(NarrativeTrading.coin_bot_id == coin.bot_id)
        elif coin_id:
            query = query.filter(NarrativeTrading.coin_bot_id == coin_id)

        total_count = query.count()
        
        narrative_trading_objects = (query.order_by(desc(NarrativeTrading.created_at))
                                     .offset((page - 1) * limit)
                                     .limit(limit)
                                     .all())

        if not narrative_trading_objects:
            return jsonify(create_response(success=False, error='No narrative trading found')), 404

        narrative_trading_data = [nt.to_dict() for nt in narrative_trading_objects]
        for nt_dict, nt in zip(narrative_trading_data, narrative_trading_objects):
            nt_dict['coin_bot_name'] = nt.coin_bot.name if nt.coin_bot else None

        total_pages = (total_count + limit - 1) // limit

        return jsonify(create_response(
            success=True, 
            data=narrative_trading_data, 
            total_count=total_count, 
            total_pages=total_pages, 
            page=page, 
            limit=limit
        )), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify(create_response(success=False, error=f"Database error occurred: {str(e)}")), 500

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, error=f"Internal server error occurred: {str(e)}")), 500

    finally:
        session.close()
        
        
@narrative_trading_bp.route('/narrative-tradings', methods=['GET'])
@cache_with_redis()
def get_all_narrative_trading():
    """
    Retrieve all narrative trading entries with optional pagination.

    Query Parameters:
    - page (int, optional): Page number for pagination
    - limit (int, optional): Number of items per page (max: 100)

    Returns:
    JSON with narrative trading data, including total count and pagination info.
    """
    response = {
        "data": None,
        "error": None,
        "success": False,
        "total": 0,
        "page": None,
        "limit": None,
        "total_pages": None
    }
    status_code = 500  # Default to server error

    session = Session()
    try:
        # Get pagination parameters
        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)

        # Build the query
        query = session.query(NarrativeTrading).options(joinedload(NarrativeTrading.coin_bot))
        query = query.order_by(desc(NarrativeTrading.created_at))

        # Get total count
        total_count = query.count()

        if total_count == 0:
            response["error"] = "No narrative trading entries found"
            status_code = 404
            return jsonify(response), status_code

        # Apply pagination only if both page and limit are provided
        if page and limit:
            if page < 1 or limit < 1:
                response["error"] = "Invalid pagination parameters"
                status_code = 400
                return jsonify(response), status_code

            limit = min(limit, 100)  # Cap at 100
            total_pages = (total_count + limit - 1) // limit
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
        else:
            total_pages = 1
            page = 1
            limit = total_count

        # Execute the query
        narrative_trading_objects = query.all()

        # Prepare the response data
        narrative_trading_data = []
        for nt in narrative_trading_objects:
            nt_dict = nt.to_dict()
            nt_dict['coin_name'] = nt.coin_bot.name if nt.coin_bot else None
            narrative_trading_data.append(nt_dict)

        response["data"] = narrative_trading_data
        response["success"] = True
        response["total"] = total_count
        response["page"] = page
        response["limit"] = limit
        response["total_pages"] = total_pages
        status_code = 200

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code


@narrative_trading_bp.route('/narrative-trading', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_narrative_trading'])
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
        coin_id = request.form.get('coin_id')
        content = request.form.get('content')
        category_name = request.form.get('category_name')
        

        if not (coin_id and content):
            return jsonify(create_response(success=False, 
                                           error='One or more required values are missing')), 400

        # Call the function to handle posting
        narrative_trading_post = publish_narrative_trading(coin_id, content, category_name)
        
        if narrative_trading_post is None:
            return jsonify(create_response(success=False, 
                                           error='Failed to publish narrative trading')), 500

        session.commit()
        return jsonify(create_response(success=True, data=narrative_trading_post, 
                                       message='Narrative Trading posted successfully')), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify(create_response(success=False, 
                                       error="Database error occurred.")), 500

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, 
                                       error="Internal server error occurred.")), 500
    finally:
        session.close()

    
@narrative_trading_bp.route('/narrative-trading/<int:narrative_trading_id>', methods=['DELETE'])
@update_cache_with_redis(related_get_endpoints=['get_all_narrative_trading'])
def delete_narrative_trading(narrative_trading_id):
    """
    Delete a narrative trading post by narrative_trading_id and its associated S3 image.

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
            return jsonify(create_response(success=False, 
                                           error='Narrative trading not found')), 404

        # Delete associated S3 image if it exists
        if narrative_trading_to_delete.image_url:
            try:
                image_processor.delete_from_s3(narrative_trading_to_delete.image_url)
            except Exception as e:
                raise ValueError(f"Error: {str(e)}")
                
        session.delete(narrative_trading_to_delete)
        session.commit()

        return jsonify(create_response(success=True, 
                                       message='Narrative trading and associated image deleted successfully')), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify(create_response(success=False, 
                                       error=f"Database error occurred: {str(e)}")), 500

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, 
                                       error=f"Internal server error while deleting: {str(e)}")), 500
    finally:
        session.close()


@narrative_trading_bp.route('/narrative-trading/<int:narrative_trading_id>', methods=['PUT'])
@update_cache_with_redis(related_get_endpoints=['get_all_narrative_trading', 'get_narrative_trading'])
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
            return jsonify(create_response(success=False, 
                                           error='Narrative trading not found')), 404

        new_content = request.json.get('content')

        if not new_content:
            return jsonify(create_response(success=False, 
                                           error='New content is required to edit the narrative trading')), 400

        narrative_trading_to_edit.narrative_trading = new_content
        session.commit()

        return jsonify(create_response(success=True, 
                                       data=narrative_trading_to_edit.to_dict(),
                                       message='Narrative trading edited successfully')), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify(create_response(success=False, 
                                       error=f"Database error occurred, {str(e)}")), 500

    except Exception as e:
        session.rollback()
        return jsonify(create_response(success=False, 
                                       error=f"Internal server error occurred, {str(e)}")), 500

    finally:
        session.close()


@narrative_trading_bp.route('/narrative-trading/last', methods=['GET'])
def get_last_narrative_trading():
    """
    Retrieve the most recent narrative trading entry.

    Returns:
    JSON with the last narrative trading data, including associated coin bot name.
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    session = Session()
    try:
        last_narrative_trading = session.query(NarrativeTrading).options(
            joinedload(NarrativeTrading.coin_bot)
        ).order_by(NarrativeTrading.created_at.desc()).first()

        if not last_narrative_trading:
            response["error"] = "No narrative trading found"
            status_code = 404
            return jsonify(response), status_code

        narrative_trading_data = last_narrative_trading.to_dict()
        narrative_trading_data['coin_bot_name'] = last_narrative_trading.coin_bot.name if last_narrative_trading.coin_bot else None

        response["data"] = {'last_narrative_trading': narrative_trading_data}
        response["success"] = True
        status_code = 200

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code

def publish_narrative_trading(coin_bot_id, content, category_name):
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
    session = Session()
    try:
        try:
            title, content = extract_title_and_content(content)
        except Exception as e:
            raise ValueError(f"Error extracting title and content: {str(e)}")

        try:
            image_url = generate_and_upload_image(title, content)
        except Exception as e:
            raise ValueError(f"Error generating and uploading image: {str(e)}")

        try:
            new_narrative_trading = create_narrative_trading(coin_bot_id, content, category_name, image_url)
        except Exception as e:
            raise ValueError(f"Error creating narrative trading: {str(e)}")

        session.commit()
        return create_response(success=True, 
                               data=new_narrative_trading.to_dict(), 
                               message='Narrative Trading posted successfully')

    except SQLAlchemyError as e:
        session.rollback()
        return create_response(success=False, error=f"Database error occurred: {str(e)}")
    except ValueError as e:
        session.rollback()
        return create_response(success=False, error=str(e))
    except Exception as e:
        session.rollback()
        return create_response(success=False, error=f"Internal server error occurred: {str(e)}")
    finally:
        session.close()
                
def extract_title_and_content(content):
    title_end_index = content.find('\n')
    if title_end_index != -1:
        title = content[:title_end_index].strip()
        content = content[title_end_index+1:]
    else:
        raise ValueError("Error extracting title and content")
    
    return title, content

def generate_and_upload_image(title, content):
    try:
        image = image_generator.generate_image(content)
        
        formatted_title = title.replace(':', '').replace(' ', '-').strip().lower()
        image_filename = f"{formatted_title}.jpg"
        resized_image_url = image_processor.process_and_upload_image(
            image_url=image,
            bucket_name='appnarrativetradingimages',
            image_filename=image_filename
        )
        if not resized_image_url:
            raise ValueError("Error resizing and uploading the image to S3")
        
        return resized_image_url
    except Exception as e:
        raise ValueError(f"Image generation and upload failed: {str(e)}")

def create_narrative_trading(coin_bot_id, content, category_name, image_url):
    with Session() as session:
        try:
            new_narrative_trading = NarrativeTrading(
                narrative_trading=content,
                category_name=category_name,
                coin_bot_id=coin_bot_id,
                image_url=image_url
            )
            session.add(new_narrative_trading)
            session.commit()
            return new_narrative_trading
        
        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Failed to save to the database: {str(e)}"
            raise ValueError(error_message)
        except Exception as e:
            session.rollback()
            error_message = f"An unexpected error occurred: {str(e)}"
            raise ValueError(error_message)
        
        
@narrative_trading_bp.route('/schedule-narrative-trading', methods=['POST'])
def schedule_post():
    """
    Schedule a narrative trading post for future publishing.

    This function receives post details via POST request, validates the input,
    and schedules the post for future publication using APScheduler.

    Args:
        None (all arguments are received via request.form)

    Form Parameters:
        coinBot (str): ID of the coin bot
        category_name (str): Name of the category
        content (str): Content of the post
        scheduledDate (str): Scheduled date and time for publishing (format: '%a, %b %d, %Y, %I:%M:%S %p')

    Returns:
        tuple: A tuple containing:
            - A JSON response with keys:
                - 'message': Success or error message
                - 'success': True if successful, False otherwise
            - HTTP status code (int)

    Raises:
        ValueError: If the date format is invalid
        Exception: For any other unexpected errors
    """
    try:
        coin_id = request.form.get('coin_id')
        category_name = request.form.get('category_name')
        content = request.form.get('content')
        scheduled_date_str = request.form.get('scheduled_date')

        missing_params = []
        if not coin_id:
            missing_params.append('coin_id')
        if not content:
            missing_params.append('content')
        if not scheduled_date_str:
            missing_params.append('scheduledDate')

        if missing_params:
            error_message = f"The following required parameters are missing: {', '.join(missing_params)}"
            return jsonify(create_response(success=False, 
                                           error=error_message)), 400

        try:
            scheduled_datetime = datetime.strptime(scheduled_date_str, '%a, %b %d, %Y, %I:%M:%S %p')
        except ValueError as e:
            return jsonify(create_response(success=False, 
                                           error=f'Invalid date format: {str(e)}')), 400

        job = sched.add_job(publish_narrative_trading, 
                            args=[coin_id, content, category_name],
                            trigger=DateTrigger(run_date=scheduled_datetime))

        return jsonify(create_response(success=True, 
                                       message=f'Post scheduled successfully - Job ID: {job.id}')), 200

    except Exception as e:
        return jsonify(create_response(success=False, 
                                       error=f'An unexpected error occurred: {str(e)}')), 500


@narrative_trading_bp.route('/scheduled-narrative-tradings', methods=['GET'])
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

        return jsonify(create_response(success=True, 
                                       data={'jobs': job_listing})), 200

    except Exception as e:
        return jsonify(create_response(success=False, 
                                       error=f"Failed to retrieve jobs, {str(e)}")), 500


@narrative_trading_bp.route('/scheduled-narrative-tradings/<string:job_id>', methods=['DELETE'])
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
            return jsonify(create_response(success=False, 
                                           error='Scheduled job not found')), 404

        sched.remove_job(job_id)
        return jsonify(create_response(success=True, 
                                       message='Scheduled job deleted successfully')), 200

    except JobLookupError as e:
        return jsonify(create_response(success=False, 
                                       error=f"Job not found, {str(e)}")), 404

    except Exception as e:
        return jsonify(create_response(success=False, 
                                       error=f"Failed to delete job, {str(e)}")), 500
    
