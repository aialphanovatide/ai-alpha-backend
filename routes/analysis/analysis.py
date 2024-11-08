
import pytz
import datetime
from sqlalchemy import desc
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple, Dict
from sqlalchemy.exc import SQLAlchemyError
from services.notification.index import Notification
from services.aws.s3 import ImageProcessor
from config import Analysis, CoinBot, Session
from flask import jsonify, Blueprint, request
from services.openai.dalle import ImageGenerator
from apscheduler.triggers.date import DateTrigger
from utils.session_management import create_response
from apscheduler.jobstores.base import JobLookupError
from routes.analysis.analysis_scheduler import sched, chosen_timezone
from redis_client.redis_client import cache_with_redis, update_cache_with_redis

analysis_bp = Blueprint('analysis_bp', __name__)

image_generator = ImageGenerator()
image_processor = ImageProcessor()
notification_service = Notification(session=Session())


@analysis_bp.route('/analysis', methods=['GET'])
@cache_with_redis()
def get_coin_analysis():
    """
    Retrieve analyses for a specific coin by ID or name, with optional pagination.

    This endpoint queries the database for analyses related to a specific coin,
    identified either by ID or name, ordered by creation date descending.

    Args:
        coin_bot_id (int): The ID of the coin bot (optional)
        coin_bot_name (str): The name of the coin bot (optional)
        page (int): The page number (default: 1)
        limit (int): The number of items per page (default: 10, max: 100)

    Returns:
        JSON: A JSON object containing:
            - data (list): List of analysis objects
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
            - total (int): Total number of analyses for this coin bot
            - page (int): Current page number (if pagination is used)
            - limit (int): Number of items per page (if pagination is used)
            - total_pages (int): Total number of pages (if pagination is used)
        HTTP Status Code

    Raises:
        400 Bad Request: If neither coin ID nor name is provided, or if invalid pagination parameters are provided
        404 Not Found: If no analyses are found for the specified coin
        500 Internal Server Error: If there's an unexpected error during execution
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
        # Get coin identification parameters
        coin_id = request.args.get('coin_id', type=int)
        coin_name = request.args.get('coin_name')

        if not coin_id and not coin_name:
            response["error"] = "Either coin_id or coin_name is required"
            status_code = 400
            return jsonify(response), status_code

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)

        # Build the query
        query = session.query(Analysis)
        if coin_id:
            query = query.filter(Analysis.coin_bot_id == coin_id)
        elif coin_name:
            coin = session.query(CoinBot).filter(CoinBot.name == coin_name).first()
            if not coin:
                response["error"] = f"No coin found with name: {coin_name}"
                status_code = 404
                return jsonify(response), status_code
            query = query.filter(Analysis.coin_bot_id == coin.bot_id)

        # Get total count
        total_analyses = query.count()

        if total_analyses == 0:
            response["error"] = "No analyses found for the specified coin"
            status_code = 404
            return jsonify(response), status_code

        # Apply pagination
        if page < 1 or limit < 1:
            response["error"] = "Invalid pagination parameters"
            status_code = 400
            return jsonify(response), status_code

        limit = min(limit, 100)  # Cap at 100
        total_pages = (total_analyses + limit - 1) // limit
        offset = (page - 1) * limit
        query = query.order_by(desc(Analysis.created_at)).offset(offset).limit(limit)

        # Execute the query
        analysis_objects = query.all()

        # Prepare the response data
        analysis_data = [analy.to_dict() for analy in analysis_objects]

        response["data"] = analysis_data
        response["success"] = True
        response["total"] = total_analyses
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


@analysis_bp.route('/analyses', methods=['GET'])
@cache_with_redis()
def get_all_analysis():
    """
    Retrieve all analyses with pagination.

    This endpoint queries the database for analyses, ordered by creation date descending.
    It supports pagination and a configurable limit.

    Args:
        page (int): The page number (default: 1)
        limit (int): The number of items per page (default: 10, max: 100)

    Returns:
        JSON: A JSON object containing:
            - data (list): List of analysis objects
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
            - total (int): Total number of analyses
            - page (int): Current page number
            - limit (int): Number of items per page
            - total_pages (int): Total number of pages
        HTTP Status Code

    Raises:
        400 Bad Request: If invalid pagination parameters are provided
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False,
        "total": 0,
        "page": 1,
        "limit": 10,
        "total_pages": 0
    }
    status_code = 500  # Default to server error

    session = Session()
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 10, type=int), 100)  # Cap at 100

        if page < 1 or limit < 1:
            response["error"] = "Invalid pagination parameters"
            status_code = 400
            return jsonify(response), status_code

        # Query for total count
        total_analyses = session.query(Analysis).count()

        # Calculate pagination values
        total_pages = (total_analyses + limit - 1) // limit
        offset = (page - 1) * limit

        # Query with pagination
        analysis_objects = session.query(Analysis)\
            .order_by(desc(Analysis.created_at))\
            .offset(offset)\
            .limit(limit)\
            .all()

        # Prepare the response data
        analysis_data = [analy.to_dict() for analy in analysis_objects]

        response["data"] = analysis_data
        response["success"] = True
        response["total"] = total_analyses
        response["page"] = page
        response["limit"] = limit
        response["total_pages"] = total_pages
        status_code = 200  # Use 200 for successful responses

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


@analysis_bp.route('/analysis', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_analysis'])
def post_analysis():
    """
    Create a new analysis and publish it.

    This endpoint creates a new analysis based on the provided data and publishes it.

    Args:
        None (data is expected in the request form)

    Expected form data:
        coin_id (str): The ID of the coin
        content (str): The content of the analysis
        category_name (str): The name of the category

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the created analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code:
            - 201: Created successfully
            - 400: Bad Request (missing or invalid data)
            - 500: Internal Server Error

    Raises:
        400 Bad Request: If required data is missing or null
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    session = Session()
    try:
        # Extract data from the request
        coin_id = request.form.get('coin_id')
        content = request.form.get('content')
        category_name = request.form.get('category_name')

        # Check if any of the required values is missing or null
        missing_params = [param for param in ['coin_id', 'content', 'category_name'] if not locals()[param] or locals()[param] == 'null']
        if missing_params:
            response["error"] = f"The following required values are missing or null: {', '.join(missing_params)}"
            response["success"] = False
            return jsonify(response), 400

        try:
            response = publish_analysis(coin_id=coin_id, 
                             content=content, 
                             category_name=category_name)

            if response["success"]:
                # Update the response data with analysis details
                response["data"] = response["data"]
                response["success"] = response["success"]
                status_code = 201   
            else:
                response["error"] = response["error"]
                status_code = 500

        except ValueError as e:
            session.rollback()
            response["error"] = f"Image processing failed: {str(e)}"
            status_code = 500
        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error: {str(e)}"
            status_code = 500
        except Exception as e:
            session.rollback()
            response["error"] = f"Unexpected error: {str(e)}"
            status_code = 500

    except Exception as e:
        response["error"] = f"Request failed: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code


@analysis_bp.route('/analysis/<int:analysis_id>', methods=['DELETE'])
@update_cache_with_redis(related_get_endpoints=['get_all_analysis'])
def delete_analysis(analysis_id):
    """
    Delete an existing analysis and its associated image.

    This endpoint removes an analysis identified by its ID and any associated image.

    Args:
        analysis_id (int): The ID of the analysis to delete

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the deleted analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        404 Not Found: If the specified analysis is not found
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    session = Session()
    try:
        # Check if the analysis_id exists
        analysis_to_delete = session.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
        if not analysis_to_delete:
            response["error"] = "Analysis not found"
            status_code = 404
            return jsonify(response), status_code

        # Delete the associated image from S3 if it exists
        if analysis_to_delete.image_url:
            try:
                image_processor.delete_from_s3(image_url=analysis_to_delete.image_url)
            except Exception as e:
                response["error"] = f"Error deleting image from S3: {str(e)}"
                return jsonify(response), 500

        # Delete the analysis
        session.delete(analysis_to_delete)
        session.commit()

        response["data"] = f'Analysis deleted successfully with its image'
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


@analysis_bp.route('/analysis/<int:analysis_id>', methods=['PUT'])
@update_cache_with_redis(related_get_endpoints=['get_all_analysis', 'get_coin_analysis'])
def edit_analysis(analysis_id):
    """
    Edit the content of an existing analysis.

    This endpoint updates the content of an analysis identified by its ID.

    Args:
        analysis_id (int): The ID of the analysis to edit

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the edited analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If the new content is not provided
        404 Not Found: If the specified analysis is not found
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    # Get and validate new content
    new_content = request.json.get('content')
    if not new_content:
        response["error"] = "New content is required to edit the Analysis"
        status_code = 400
        return jsonify(response), status_code

    session = Session()
    try:
        # Check if the analysis_id exists
        analysis_to_edit = session.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
        if analysis_to_edit is None:
            response["error"] = "Analysis not found"
            status_code = 404
            return jsonify(response), status_code

        # Update analysis content
        analysis_to_edit.analysis = new_content
        session.commit()

        # Prepare the response data
        response["data"] = analysis_to_edit.to_dict()
        response["success"] = True
        status_code = 200  # Use 200 for successful update

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


@analysis_bp.route('/analysis/last', methods=['GET'])
@cache_with_redis()
def get_last_analysis():
    """
    Retrieve the name and date of the last analysis created.

    This endpoint queries the database for the most recently created analysis
    and returns its details along with the associated coin information.

    Args:
        None

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the last analysis, if found
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        404 Not Found: If no analysis is found or the associated coin is not found
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    session = Session()
    try:
        # Retrieve the last analysis created
        last_analysis = session.query(Analysis).order_by(desc(Analysis.created_at)).first()

        if last_analysis is None:
            response["error"] = "No analysis found"
            status_code = 404
            return jsonify(response), status_code

        # Prepare the response data
        response["data"] = last_analysis.to_dict()
        response["success"] = True
        status_code = 200
        return jsonify(response), status_code

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
    
   
def publish_analysis(coin_id: int, content: str, category_name: str) -> dict:
    """
    Function to publish an analysis.

    Args:
        coin_id (int): The ID of the coin bot
        content (str): The content of the analysis
        category_name (str): The name of the category

    Returns:
        dict: A response dictionary containing the result of the operation
    """
    session = Session()
    image_filename = None
    try:
        # Extract title and adjust content
        title_end_index = content.find('<br>')
        if title_end_index != -1:
            title = content[:title_end_index].strip()
            content = content[title_end_index + 4:].strip()  # +4 to remove '<br>'
        else:
            raise ValueError("No newline found in the content, please add a space after the title")

        # Extract title and format it
        title = BeautifulSoup(title, 'html.parser').get_text()
        formatted_title = title.replace(':', '').replace(' ', '-').strip().lower()
        image_filename = f"{formatted_title}.jpg"

        # Generate image
        try:
            image = image_generator.generate_image(content)
        except Exception as e:
            raise ValueError(f"Image generation failed: {str(e)}")
        
        try:
            resized_image_url = image_processor.process_and_upload_image(
                image_url=image,
                bucket_name='appanalysisimages',
                image_filename=image_filename
            )
        except Exception as e:
            raise ValueError(f"Image processing failed: {str(e)}")

        # Query the database to get the coin_bot name
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()
        if not coin_bot:
            raise ValueError(f"No CoinBot found with id {coin_id}")
        
        coin_symbol = coin_bot.name

        # Create and save the Analysis object
        new_analysis = Analysis(
            analysis=content,
            category_name=category_name,
            coin_bot_id=coin_id,
            image_url=resized_image_url
        )
        session.add(new_analysis)
        session.commit()
        

        # Send notification
        notification_service.push_notification(
            coin=coin_symbol,
            title=f"{str(coin_symbol).upper()} New Analysis Available",  
            body=f"{title} - Check it out!",
            type="analysis",
            timeframe=""  
        )
        
        return create_response(
            data=new_analysis.to_dict(),
            message="Analysis published successfully",
            success=True,
            status_code=201
        )
        
    except SQLAlchemyError as e:
        session.rollback()
        return create_response(
            data=None,
            message=f"Database error publishing analysis: {str(e)}",
            success=False,
            status_code=500
        )
    except ValueError as e:
        return create_response(
            data=None,
            message=f"Value error publishing analysis: {str(e)}",
            success=False,
            status_code=400
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"Unexpected error publishing analysis: {str(e)}",
            success=False,
            status_code=500
        )
    finally:
        session.close()


# ____________________________________ Scheduled Analysis Endpoints __________________________________________________________
        
@analysis_bp.route('/scheduled-analyses', methods=['POST'])
def schedule_post() -> Tuple[Dict, int]:
    """
    Schedule a post for future publication.

    This endpoint allows scheduling an analysis post for a specific coin bot at a future date and time.
    It validates the input data, checks if the scheduled time is in the future, and adds the job to the scheduler.

    Expected JSON payload:
        coin_id (int): The ID of the coin bot
        category_name (str): The name of the category
        content (str): The content of the post
        scheduled_date (str): The scheduled date and time in ISO 8601 format (e.g., '2023-01-01T12:00:00.000Z')

    Returns:
        Tuple[Dict, int]: A tuple containing:
            - Dict: JSON response with the following keys:
                - message (str): Success message if the post was scheduled
                - error (str): Error message if there was a problem
                - success (bool): True if the post was scheduled successfully, False otherwise
                - job_id (str): The ID of the scheduled job (if successful)
            - int: HTTP status code
                - 201: Post scheduled successfully
                - 400: Bad request (missing or invalid data)
                - 500: Server error

    Raises:
        ValueError: If the date format is invalid
        Exception: For any unexpected errors during execution

    Note:
        The scheduled date is expected to be in UTC and will be converted to the chosen timezone
        (America/Argentina/Buenos_Aires) for scheduling.
    """
    response = {"message": None, "error": None, "success": False, "job_id": None}
    status_code = 500  # Default to server error

    try:
        coin_id = request.form.get('coin_id')
        category_name = request.form.get('category_name')
        content = request.form.get('content')
        scheduled_date = request.form.get('scheduled_date')

        missing_params = []
        if not coin_id:
            missing_params.append("coin_id")
        if not category_name:
            missing_params.append("category_name")
        if not content:
            missing_params.append("content")
        if not scheduled_date:
            missing_params.append("scheduled_date")
        
        if missing_params:
            response["error"] = f"The following required values are missing: {', '.join(missing_params)}"
            status_code = 400
            return jsonify(response), status_code

        try:
            coin_id = int(coin_id)
            # Parse the ISO 8601 format as UTC, then convert to Buenos Aires time
            scheduled_datetime = datetime.strptime(scheduled_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            scheduled_datetime = pytz.utc.localize(scheduled_datetime).astimezone(chosen_timezone)

            # Get current time in Buenos Aires
            current_time = datetime.now(chosen_timezone)

            if scheduled_datetime <= current_time:
                response["error"] = "Scheduled date must be in the future"
                status_code = 400
                return jsonify(response), status_code

        except ValueError as e:
            response["error"] = f"Invalid date format. Expected 'YYYY-MM-DDTHH:MM:SS.sssZ': {str(e)}"
            status_code = 400
            return jsonify(response), status_code


        job = sched.add_job(
            publish_analysis, 
            args=[coin_id, content, category_name], 
            trigger=DateTrigger(run_date=scheduled_datetime)
        )

        response["message"] = "Post scheduled successfully"
        response["job_id"] = job.id
        response["success"] = True
        status_code = 201

    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@analysis_bp.route('/scheduled-analyses/<string:job_id>', methods=['DELETE'])
def delete_scheduled_job(job_id):
    """
    Delete a scheduled job by its ID.

    Args:
        job_id (str): The ID of the scheduled job to delete.

    Returns:
        JSON response with status code:
        - 201: Job deleted successfully
        - 404: Job not found
        - 500: Server error
    """
    response = {"message": None, "error": None, "success": False}
    status_code = 500  # Default to server error

    try:
        # Find the scheduled job by ID
        job = sched.get_job(job_id)
        
        if job is None:
            response["error"] = "Scheduled job not found"
            status_code = 404
        else:
            # Delete the job
            sched.remove_job(job_id)
            response["message"] = "Scheduled job deleted successfully"
            response["success"] = True
            status_code = 201

    except JobLookupError as e:
        response["error"] = f"Error looking up job: {str(e)}"
        status_code = 404
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    
    return jsonify(response), status_code


@analysis_bp.route('/scheduled-analyses/<string:job_id>', methods=['GET'])
def get_scheduled_job(job_id):
    """
    Get information about a scheduled job by its ID.

    Args:
        job_id (str): The ID of the scheduled job to retrieve.

    Returns:
        JSON response with status code:
        - 201: Job information retrieved successfully
        - 404: Job not found
        - 500: Server error
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 500  # Default to server error
    
    try:
        job = sched.get_job(job_id)
        
        if job is None:
            response["error"] = "Scheduled job not found"
            status_code = 404
        else:
            response["data"] = {
                "id": job.id,
                "name": job.name,
                "func": str(job.func),
                "trigger": str(job.trigger),
                'args': str(job.args),
                "next_run_time": str(job.next_run_time) if hasattr(job, 'next_run_time') else None
            }
            response["success"] = True
            status_code = 201

    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    
    return jsonify(response), status_code


@analysis_bp.route('/scheduled-analyses', methods=['GET'])
def get_scheduled_jobs():
    """
    Retrieve information about all scheduled jobs.

    Returns:
        JSON response with status code:
        - 200: Jobs information retrieved successfully
        - 500: Server error
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 500  # Default to server error

    try:
        job_listing = []
        for job in sched.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'args': str(job.args),
                'next_run_time': str(job.next_run_time) if job.next_run_time else None
            }
            job_listing.append(job_info)

        response["data"] = {"jobs": job_listing}
        response["success"] = True
        status_code = 200

    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code
    
    
