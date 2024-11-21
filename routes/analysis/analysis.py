
import pytz
import datetime
from sqlalchemy import desc
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple, Dict, Type
from sqlalchemy.exc import SQLAlchemyError
from services.notification.index import Notification
from services.aws.s3 import ImageProcessor
from config import Analysis, CoinBot, Session
from flask import current_app, jsonify, Blueprint, request
from services.openai.dalle import ImageGenerator
from apscheduler.triggers.date import DateTrigger
from utils.session_management import create_response
from apscheduler.jobstores.base import JobLookupError
from config import Analysis, Category, CoinBot, NarrativeTrading, SAndRAnalysis, Sections, Session
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
    Retrieve analyses for a specific coin by ID, with optional pagination.

    This endpoint queries the appropriate table based on the section target
    for analyses related to a specific coin, identified by ID.

    Args:
        coin_bot_id (int): The ID of the coin bot (required)
        section_id (int): The ID of the section (required)
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
        # Get required parameters
        coin_bot_id = request.args.get('coin_bot_id', type=int)
        section_id = request.args.get('section_id', type=int)

        if not coin_bot_id or not section_id:
            response["error"] = "Both coin_bot_id and section_id are required"
            status_code = 400
            return jsonify(response), status_code

        # Get section information
        section = session.query(Sections).filter_by(id=section_id).first()
        if not section:
            response["error"] = f"Section with id {section_id} not found"
            status_code = 404
            return jsonify(response), status_code

        # Get the corresponding model based on target
        target = section.target.lower()
        model_class = MODEL_MAPPING.get(target)
        if not model_class:
            response["error"] = f"No model found for target: {section.target}"
            status_code = 400
            return jsonify(response), status_code

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 10, type=int), 100)  # Cap at 100

        if page < 1 or limit < 1:
            response["error"] = "Invalid pagination parameters"
            status_code = 400
            return jsonify(response), status_code

        # Build the query
        query = session.query(model_class).filter(model_class.coin_bot_id == coin_bot_id)

        # Get total count
        total_analyses = query.count()

        if total_analyses == 0:
            response["error"] = "No analyses found for the specified coin and section"
            status_code = 404
            return jsonify(response), status_code

        # Apply pagination
        total_pages = (total_analyses + limit - 1) // limit
        offset = (page - 1) * limit
        query = query.order_by(desc(model_class.created_at)).offset(offset).limit(limit)

        # Execute the query
        analysis_objects = query.all()

        # Prepare the response data
        analysis_data = [analy.to_dict() for analy in analysis_objects]

        response.update({
            "data": analysis_data,
            "success": True,
            "total": total_analyses,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        })
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
    Retrieve all analyses with pagination based on section.
    
    Args:
        section_id (str): The ID of the section to get analyses from
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
        
    Raises:
        400 Bad Request: If invalid parameters are provided
        404 Not Found: If section is not found
        500 Internal Server Error: If there's an unexpected error
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
        # Get required parameters
        section_id = request.args.get('section_id')
        if not section_id:
            response["error"] = "section_id is required"
            status_code = 400
            return jsonify(response), status_code

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 10, type=int), 100)  # Cap at 100
        
        if page < 1 or limit < 1:
            response["error"] = "Invalid pagination parameters"
            status_code = 400
            return jsonify(response), status_code

        # Get section information
        section = session.query(Sections).filter_by(id=section_id).first()
        if not section:
            response["error"] = f"Section with id {section_id} not found"
            status_code = 404
            return jsonify(response), status_code

        # Get the corresponding model based on target
        target = section.target.lower()
        model_class = MODEL_MAPPING.get(target)
        if not model_class:
            response["error"] = f"No model found for target: {section.target}"
            status_code = 400
            return jsonify(response), status_code

        # Query for total count
        total_analyses = session.query(model_class).count()

        # Calculate pagination values
        total_pages = (total_analyses + limit - 1) // limit
        offset = (page - 1) * limit

        # Query with pagination
        analysis_objects = session.query(model_class)\
            .order_by(desc(model_class.created_at))\
            .offset(offset)\
            .limit(limit)\
            .all()

        # Prepare the response data
        analysis_data = [analy.to_dict() for analy in analysis_objects]

        # Update response
        response.update({
            "data": analysis_data,
            "success": True,
            "total": total_analyses,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "section_name": section.name,  # Incluimos el nombre de la sección
            "section_target": section.target  # Incluimos el target para referencia
        })
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

@analysis_bp.route('/analysis', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_analysis'])
def post_analysis():
    """
    Create a new analysis and publish it.
    ...
    """
    current_app.logger.debug(f"Received POST request to /analysis")
    
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error
    session = Session()
    
    try:
        # Extract data from the request
        section_id = request.form.get("section_id")
        coin_id = request.form.get('coin_id')
        content = request.form.get('content')
        category_name = request.form.get('category_name')
        
        current_app.logger.debug(f"Received parameters: section_id={section_id}, coin_id={coin_id}, category_name={category_name}")
        
        # Check if any of the required values is missing or null
        missing_params = [param for param in ['coin_id', 'content', 'category_name'] if not locals()[param] or locals()[param] == 'null']
        
        if missing_params:
            current_app.logger.debug(f"Missing parameters: {missing_params}")
            response["error"] = f"The following required values are missing or null: {', '.join(missing_params)}"
            response["success"] = False
            return jsonify(response), 400
        
        try:
            response = publish_analysis(
                coin_id=coin_id,
                section_id=section_id,
                content=content,
                category_name=category_name
            )
            
            current_app.logger.debug(f"Publish analysis response: {response}")
            
            if response["success"]:
                response["data"] = response["data"]
                response["success"] = response["success"]
                status_code = 201
            else:
                current_app.logger.error(f"Failed to publish analysis: {response['error']}")
                response["error"] = response["error"]
                status_code = 500
        
        except ValueError as e:
            session.rollback()
            current_app.logger.error(f"Image processing failed: {str(e)}")
            response["error"] = f"Image processing failed: {str(e)}"
            status_code = 500
        
        except SQLAlchemyError as e:
            session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            response["error"] = f"Database error: {str(e)}"
            status_code = 500
        
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Unexpected error: {str(e)}")
            response["error"] = f"Unexpected error: {str(e)}"
            status_code = 500
    
    except Exception as e:
        current_app.logger.error(f"Request failed: {str(e)}")
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

    This endpoint removes an analysis identified by its ID and section, and any associated image.

    Args:
        analysis_id (int): The ID of the analysis to delete

    Query Parameters:
        section_id (int): The ID of the section the analysis belongs to

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the deleted analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If section_id is not provided
        404 Not Found: If the specified analysis or section is not found
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
        # Get section_id from query parameters
        section_id = request.args.get('section_id', type=int)
        if not section_id:
            response["error"] = "section_id is required"
            status_code = 400
            return jsonify(response), status_code

        # Get section information
        section = session.query(Sections).filter_by(id=section_id).first()
        if not section:
            response["error"] = f"Section with id {section_id} not found"
            status_code = 404
            return jsonify(response), status_code

        # Get the corresponding model based on target
        target = section.target.lower()
        model_class = MODEL_MAPPING.get(target)
        if not model_class:
            response["error"] = f"No model found for target: {section.target}"
            status_code = 400
            return jsonify(response), status_code

        # Check if the analysis exists
        analysis_to_delete = session.query(model_class).filter(model_class.id == analysis_id).first()
        if not analysis_to_delete:
            response["error"] = f"Analysis not found in {section.target} table"
            status_code = 404
            return jsonify(response), status_code

        # Delete the associated image from S3 if it exists
        if hasattr(analysis_to_delete, 'image_url') and analysis_to_delete.image_url:
            try:
                image_processor.delete_from_s3(image_url=analysis_to_delete.image_url)
            except Exception as e:
                response["error"] = f"Error deleting image from S3: {str(e)}"
                return jsonify(response), 500

        # Delete the analysis
        session.delete(analysis_to_delete)
        session.commit()

        response["data"] = f'Analysis deleted successfully from {section.target} table'
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

    This endpoint updates the content of an analysis identified by its ID and section.

    Args:
        analysis_id (int): The ID of the analysis to edit

    Query Parameters:
        section_id (int): The ID of the section the analysis belongs to

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the edited analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If the new content is not provided or section_id is missing
        404 Not Found: If the specified analysis or section is not found
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

    # Get section_id from query parameters
    section_id = request.args.get('section_id', type=int)
    if not section_id:
        response["error"] = "section_id is required"
        status_code = 400
        return jsonify(response), status_code

    session = Session()
    try:
        # Get section information
        section = session.query(Sections).filter_by(id=section_id).first()
        if not section:
            response["error"] = f"Section with id {section_id} not found"
            status_code = 404
            return jsonify(response), status_code

        # Get the corresponding model based on target
        target = section.target.lower()
        model_class = MODEL_MAPPING.get(target)
        if not model_class:
            response["error"] = f"No model found for target: {section.target}"
            status_code = 400
            return jsonify(response), status_code

        # Check if the analysis exists
        analysis_to_edit = session.query(model_class).filter(model_class.id == analysis_id).first()
        if analysis_to_edit is None:
            response["error"] = f"Analysis not found in {section.target} table"
            status_code = 404
            return jsonify(response), status_code

        # Update analysis content
        # Assuming the content field is named 'analysis' in all tables. Adjust if necessary.
        setattr(analysis_to_edit, 'analysis', new_content)
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


# Definimos un mapeo entre los targets y los modelos correspondientes
MODEL_MAPPING = {
    'analysis': Analysis,
    'narrative_trading': NarrativeTrading,
    's_and_r_analysis': SAndRAnalysis
    }

def get_section_info(session, section_id: int):
    """
    Obtiene la información de la sección por su ID
    """
    return session.query(Sections).filter(Sections.id == section_id).first()

def create_content_object(model_class: Type, content_data: Dict):
    """
    Crea una instancia del modelo correspondiente con los datos proporcionados
    """
    return model_class(
        analysis=content_data.get('analysis'),
        category_name=content_data.get('category_name'),
        coin_bot_id=content_data.get('coin_bot_id'),
        image_url=content_data.get('image_url')
    )
def publish_analysis(coin_id: int, content: str, category_name: str, section_id: str) -> dict:
    """
    Function to publish an analysis.
    Args:
        coin_id (int): The ID of the coin bot
        content (str): The content of the analysis
        category_name (str): The name of the category
        section_id (str): The ID of the section
    Returns:
        dict: A response dictionary containing the result of the operation
    """
    session = Session()
    image_filename = None
    
    current_app.logger.info(f"Starting publish_analysis for coin_id: {coin_id}, category: {category_name}, section_id: {section_id}")
    
    try:
        # Get section information
        section = get_section_info(session, section_id)
        if not section:
            current_app.logger.error(f"No Section found with id {section_id}")
            raise ValueError(f"No Section found with id {section_id}")

        # Get the corresponding model based on target
        target = section.target.lower()
        current_app.logger.debug(f"Target: {target}")
        model_class = MODEL_MAPPING.get(target)
        current_app.logger.debug(f"Model class: {model_class}")
        if not model_class:
            current_app.logger.error(f"Invalid target type: {target}")
            raise ValueError(f"Invalid target type: {target}")

        # Extract title and adjust content
        title_end_index = content.find('<br>')
        if title_end_index != -1:
            title = content[:title_end_index].strip()
            content = content[title_end_index + 4:].strip()  # +4 to remove '<br>'
        else:
            current_app.logger.error("No newline found in the content")
            raise ValueError("No newline found in the content, please add a space after the title")

        # Extract title and format it
        title = BeautifulSoup(title, 'html.parser').get_text()
        formatted_title = title.replace(':', '').replace(' ', '-').strip().lower()
        image_filename = f"{formatted_title}.jpg"
        current_app.logger.debug(f"Formatted title: {formatted_title}")

        # Generate image
        try:
            current_app.logger.info("Generating image")
            image = image_generator.generate_image(content)
        except Exception as e:
            current_app.logger.error(f"Image generation failed: {str(e)}")
            raise ValueError(f"Image generation failed: {str(e)}")

        try:
            current_app.logger.info("Processing and uploading image")
            resized_image_url = image_processor.process_and_upload_image(
                image_url=image,
                bucket_name='appanalysisimages',
                image_filename=image_filename
            )
            current_app.logger.debug(f"Resized image URL: {resized_image_url}")
        except Exception as e:
            current_app.logger.error(f"Image processing failed: {str(e)}")
            raise ValueError(f"Image processing failed: {str(e)}")

        # Query the database to get the coin_bot name
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()
        if not coin_bot:
            current_app.logger.error(f"No CoinBot found with id {coin_id}")
            raise ValueError(f"No CoinBot found with id {coin_id}")
        
        coin_symbol = coin_bot.name
        current_app.logger.debug(f"Coin symbol: {coin_symbol}")

        # Prepare content data
        content_data = {
            'analysis': content,
            'category_name': category_name,
            'coin_bot_id': coin_id,
            'image_url': resized_image_url
        }

        # Create and save the content object
        current_app.logger.info("Creating and saving content object")
        new_content = create_content_object(model_class, content_data)
        session.add(new_content)
        session.commit()
        current_app.logger.debug("Content object saved successfully")

        # Send notification
        current_app.logger.info("Sending notification")
        notification_service.push_notification(
            coin=coin_symbol,
            title=f"{str(coin_symbol).upper()} New {section.name} Available",
            body=f"{title} - Check it out!",
            type=target,
            timeframe=""
        )

        current_app.logger.info(f"{section.name} published successfully")
        return create_response(
            data=new_content.to_dict(),
            message=f"{section.name} published successfully",
            success=True,
            status_code=201
        )

    except SQLAlchemyError as e:
        session.rollback()
        current_app.logger.error(f"Database error publishing {target if 'target' in locals() else 'analysis'}: {str(e)}")
        return create_response(
            data=None,
            message=f"Database error publishing {target if 'target' in locals() else 'analysis'}: {str(e)}",
            success=False,
            status_code=500
        )
    except ValueError as e:
        current_app.logger.error(f"Value error publishing {target if 'target' in locals() else 'analysis'}: {str(e)}")
        return create_response(
            data=None,
            message=f"Value error publishing {target if 'target' in locals() else 'analysis'}: {str(e)}",
            success=False,
            status_code=400
        )
    except Exception as e:
        current_app.logger.error(f"Unexpected error publishing {target if 'target' in locals() else 'analysis'}: {str(e)}")
        return create_response(
            data=None,
            message=f"Unexpected error publishing {target if 'target' in locals() else 'analysis'}: {str(e)}",
            success=False,
            status_code=500
        )
    finally:
        session.close()
        current_app.logger.info("Finished publish_analysis function")
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
        section_id(int): The ID of section
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
        section_id = request.form.get('section_id')
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
            args=[coin_id, content, category_name, section_id], 
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
    
    
