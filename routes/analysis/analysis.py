import pytz
import datetime
from sqlalchemy import desc, func, or_
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Tuple, Dict, Type
from sqlalchemy.exc import SQLAlchemyError
from services.notification.index import NotificationService
from services.aws.s3 import ImageProcessor
from config import Analysis, CoinBot, Session
from flask import current_app, jsonify, Blueprint, request
from services.openai.dalle import ImageGenerator
from apscheduler.triggers.date import DateTrigger
from utils.session_management import create_response
from apscheduler.jobstores.base import JobLookupError
from config import Analysis, CoinBot, NarrativeTrading, SAndRAnalysis, Sections, Session, DailyMacroAnalysis, SpotlightAnalysis, Category
from ws.socket import emit_notification
from routes.analysis.analysis_scheduler import sched, chosen_timezone
from utils.logging import setup_logger

analysis_bp = Blueprint('analysis_bp', __name__)
logger = setup_logger(__name__)

image_generator = ImageGenerator()
image_processor = ImageProcessor()
notification_service = NotificationService()


@analysis_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_single_analysis(analysis_id):
    """
    Retrieve a single analysis by its ID with enriched data.
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500

    # Define column mappings for each model
    COLUMN_MAPPINGS = {
        'deep_dive': {
            'content': 'analysis',
            'id': 'analysis_id'
        },
        'daily_macro': {
            'content': 'content',
            'id': 'id'
        },
        'narratives': {
            'content': 'narrative_trading',
            'id': 'narrative_trading_id'
        },
        'spotlight': {
            'content': 'content',
            'id': 'id'
        },
        'support_resistance': {
            'content': 'analysis',
            'id': 'analysis_id'
        }
    }

    session = Session()
    try:
        # Get and validate section_id
        section_id = request.args.get('section_id', type=int)
        if not section_id:
            response["error"] = "section_id is required"
            return jsonify(response), 400

        # Get section information
        section = session.query(Sections).filter_by(id=section_id).first()
        if not section:
            response["error"] = f"Section with id {section_id} not found"
            return jsonify(response), 404

        # Get the corresponding model based on target
        target = section.target.lower()
        model_class = MODEL_MAPPING.get(target)
        if not model_class:
            response["error"] = f"No model found for target: {section.target}"
            return jsonify(response), 400

        # Get the correct column mappings for this target
        column_mapping = COLUMN_MAPPINGS.get(target)
        if not column_mapping:
            response["error"] = f"No column mapping found for target: {target}"
            return jsonify(response), 400

        # First get the analysis using the correct ID column
        id_column = getattr(model_class, column_mapping['id'])
        analysis = session.query(model_class).filter(id_column == analysis_id).first()
        if not analysis:
            response["error"] = f"Analysis with id {analysis_id} not found"
            return jsonify(response), 404

        # Get coin information
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == analysis.coin_bot_id).first()
        
        # Get category information
        category = session.query(Category).filter(func.lower(Category.name) == func.lower(analysis.category_name)).first()

        # Get content using correct column name
        content_text = getattr(analysis, column_mapping['content'])

        # Extract title from content
        title_end_index = content_text.find('<br>')
        title = content_text[:title_end_index].strip() if title_end_index != -1 else ""
        content_body = content_text[title_end_index + 4:].strip() if title_end_index != -1 else content_text

        # Clean title from HTML tags
        title = BeautifulSoup(title, 'html.parser').get_text()

        # Prepare the response data
        response["data"] = {
            "id": analysis_id,
            "coin_id": analysis.coin_bot_id,
            "coin_name": coin_bot.name if coin_bot else "",
            "coin_icon": coin_bot.icon if coin_bot else "",
            "section_name": section.name,
            "section_id": section_id,
            "title": title,
            "content": content_body,
            "image_url": analysis.image_url,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "category_name": analysis.category_name,
            "category_icon": category.icon if category else None
        }
        response["success"] = True
        status_code = 200

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in get_single_analysis: {str(e)}")
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in get_single_analysis: {str(e)}")
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()
        return jsonify(response), status_code

@analysis_bp.route('/analysis', methods=['POST'])
def post_analysis():
    """
    Create a new analysis with a pre-generated image.
    
    Request Body:
        coin_id (int): The ID of the coin
        section_id (int): The ID of the section
        content (str): The analysis content
        category_name (str): The category name
        image_url (str): The pre-generated image URL
    """
    current_app.logger.debug(f"Received POST request to /analysis")
    
    response = {
        "data": None,
        "error": None,
        "success": False
    }

    try:
        # Extract and validate required data from the request
        data = {
            'coin_id': request.form.get('coin_id'),
            'section_id': request.form.get('section_id'),
            'content': request.form.get('content'),
            'category_name': request.form.get('category_name'),
            'image_url': request.form.get('image_url')
        }

        # Log received parameters
        current_app.logger.debug(f"Received parameters: {', '.join(f'{k}={v}' for k, v in data.items())}")

        # Validate required parameters
        missing_params = [k for k, v in data.items() if not v]
        
        if missing_params:
            current_app.logger.warning(f"Missing parameters: {missing_params}")
            response["error"] = f"Missing required parameters: {', '.join(missing_params)}"
            return jsonify(response), 400

        # Convert coin_id and section_id to int
        try:
            data['coin_id'] = int(data['coin_id'])
            data['section_id'] = int(data['section_id'])
        except (ValueError, TypeError):
            current_app.logger.error(f"Invalid coin_id or section_id format")
            response["error"] = "coin_id and section_id must be valid integers"
            return jsonify(response), 400

        # Call publish_analysis with validated data
        result = publish_analysis(
            coin_id=data['coin_id'],
            section_id=data['section_id'],
            content=data['content'],
            category_name=data['category_name'],
            image_url=data['image_url']
        )

        if result.get("success"):
            return jsonify(result), 201
        else:
            current_app.logger.error(f"Failed to publish analysis: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        current_app.logger.error(f"Request failed: {str(e)}", exc_info=True)
        response["error"] = f"An unexpected error occurred: {str(e)}"
        return jsonify(response), 500


@analysis_bp.route('/analysis/<int:analysis_id>', methods=['DELETE'])
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

    try:
        with Session() as session:
            # Get section to determine model class
            section_id = request.args.get('section_id', type=int)
            if not section_id:
                raise ValueError("section_id is required")

            section = session.query(Sections).filter_by(id=section_id).first()
            if not section:
                raise ValueError(f"Section with id {section_id} not found")

            # Get the corresponding model
            model_class = MODEL_MAPPING.get(section.target.lower())
            if not model_class:
                raise ValueError(f"Invalid section target: {section.target}")

            # Use get() which automatically uses the primary key
            analysis = session.query(model_class).get(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with id {analysis_id} not found")

            # Delete the associated image from S3 if it exists
            if hasattr(analysis, 'image_url') and analysis.image_url:
                try:
                    image_processor.delete_from_s3(image_url=analysis.image_url,
                                                    bucket='appanalysisimages'
                                                    )
                except Exception as e:
                    response["error"] = f"Error deleting image from S3: {str(e)}"
                    return jsonify(response), 500

            session.delete(analysis)
            session.commit()

            response["message"] = "Analysis deleted successfully"
            response["success"] = True
            return jsonify(response), 200

    except ValueError as e:
        response["error"] = str(e)
        return jsonify(response), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting analysis: {str(e)}")
        response["error"] = "An error occurred while deleting the analysis"
        return jsonify(response), 500


@analysis_bp.route('/analysis/<int:analysis_id>', methods=['PUT'])
def edit_analysis(analysis_id):
    """
    Updates the content of an existing analysis.

    This endpoint modifies the content of an analysis identified by its ID and section.

    Args:
        analysis_id (int): The ID of the analysis to update

    Request Body:
        content (str): The new content for the analysis
        section_id (int): The ID of the section the analysis belongs to

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the updated analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If the new content or section_id is missing
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
        response["error"] = "New content is required to update the Analysis"
        status_code = 400
        return jsonify(response), status_code

    # Get section_id from request body
    section_id = request.json.get('section_id')
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
        analysis_to_edit = session.query(model_class).get(analysis_id)
        if analysis_to_edit is None:
            response["error"] = f"Analysis not found in {section.target} table"
            status_code = 404
            return jsonify(response), status_code

        # Update analysis content
        setattr(analysis_to_edit, 'analysis', new_content)
        session.commit()

        response["data"] = analysis_to_edit.to_dict()
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



@analysis_bp.route('/analyses', methods=['GET'])
def get_analyses():
    """
    Retrieve latest analyses across all analysis types with advanced filtering and search capabilities.
    
    Query Parameters:
        page (int): Page number for pagination (default: 1)
        per_page (int): Number of items per page (default: 10, max: 100)
        search (str): Search term to filter analyses by content or title
        coin (str): Filter analyses by specific coin name
        category (str): Filter analyses by category name
        section_id (int): Filter analyses by specific section ID
    
    Returns:
        JSON: {
            "data": [{
                "id": int,
                "coin_id": int,
                "coin_name": str,
                "coin_icon": str,
                "section_name": str,
                "section_id": int,
                "title": str,
                "content": str,
                "image_url": str,
                "created_at": str,    # ISO format datetime
                "category_name": str,
                "category_icon": str
            }],
            "meta": {
                "page": int,
                "per_page": int,
                "total_items": int,
                "total_pages": int
            },
            "error": str or None,
            "success": bool
        }
    """
    response = {
        "data": None,
        "meta": {
            "page": 1,
            "per_page": 10,
            "total_items": 0,
            "total_pages": 0
        },
        "error": None,
        "success": False
    }

    try:
        # Get and validate query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '').strip()
        coin_name = request.args.get('coin', '').strip()
        category = request.args.get('category', '').strip()
        section_id = request.args.get('section_id', type=int)

        # Validate pagination parameters
        if page < 1 or per_page < 1:
            return jsonify({**response, "error": "Invalid pagination parameters"}), 400

        with Session() as session:
            # Define column mappings for each model
            COLUMN_MAPPINGS = {
                'deep_dive': {
                    'content': 'analysis',
                    'id': 'analysis_id'
                },
                'daily_macro': {
                    'content': 'content',
                    'id': 'id'
                },
                'narratives': {
                    'content': 'narrative_trading',
                    'id': 'narrative_trading_id'
                },
                'spotlight': {
                    'content': 'content',
                    'id': 'id'
                },
                'support_resistance': {
                    'content': 'analysis',
                    'id': 'analysis_id'
                }
            }

            # Pre-fetch reference data
            coins_dict = {
                coin.bot_id: {
                    'name': coin.name,
                    'icon': coin.icon
                } for coin in session.query(CoinBot).all()
            }

            categories_dict = {
                category.name.lower(): {
                    'name': category.name,
                    'icon': category.icon
                } for category in session.query(Category).all()
            }

            sections_dict = {
                section.target.lower(): {
                    'id': section.id,
                    'name': section.name
                } for section in session.query(Sections).all()
            }

            # Validate section_id if provided
            target_filter = None
            if section_id:
                section = session.query(Sections).filter_by(id=section_id).first()
                if not section:
                    return jsonify({**response, "error": f"Section with id {section_id} not found"}), 404
                target_filter = section.target.lower()

            # Get coin_id from coin_name if provided
            coin_id = None
            if coin_name:
                for cid, coin_data in coins_dict.items():
                    if coin_data['name'].lower() == coin_name.lower():
                        coin_id = cid
                        break
                if coin_id is None:
                    return jsonify({**response, "error": f"Coin with name '{coin_name}' not found"}), 404

            all_results = []

            # Query each analysis type
            for target, model_class in MODEL_MAPPING.items():
                # Skip if filtering by section and this isn't the target section
                if target_filter and target != target_filter:
                    continue

                try:
                    query = session.query(model_class)

                    # Apply filters
                    if coin_id is not None:
                        query = query.filter(model_class.coin_bot_id == coin_id)
                    if category:
                        query = query.filter(func.lower(model_class.category_name) == category.lower())
                    if search:
                        content_column = COLUMN_MAPPINGS[target]['content']
                        query = query.filter(getattr(model_class, content_column).ilike(f"%{search}%"))

                    # Get results
                    analyses = query.order_by(desc(model_class.created_at)).all()

                    # Transform results to match single analysis format
                    for analysis in analyses:
                        # Skip if missing reference data
                        if (analysis.coin_bot_id not in coins_dict or 
                            analysis.category_name.lower() not in categories_dict or 
                            target not in sections_dict):
                            continue

                        coin_data = coins_dict[analysis.coin_bot_id]
                        category_data = categories_dict[analysis.category_name.lower()]
                        section_data = sections_dict[target]

                        # Get content and id using correct column names
                        content_column = COLUMN_MAPPINGS[target]['content']
                        id_column = COLUMN_MAPPINGS[target]['id']
                        
                        content_text = getattr(analysis, content_column)
                        analysis_id = getattr(analysis, id_column)

                        # Extract and clean title from content
                        title_end_index = content_text.find('<br>')
                        title = content_text[:title_end_index].strip() if title_end_index != -1 else ""
                        content = content_text[title_end_index + 4:].strip() if title_end_index != -1 else content_text
                        
                        title = BeautifulSoup(title, 'html.parser').get_text()

                        all_results.append({
                            "id": analysis_id,
                            "coin_id": analysis.coin_bot_id,
                            "coin_name": coin_data['name'],
                            "coin_icon": coin_data['icon'],
                            "section_name": section_data['name'],
                            "section_id": section_data['id'],
                            "title": title,
                            "content": content,
                            "image_url": analysis.image_url,
                            "created_at": analysis.created_at.isoformat(),
                            "category_name": category_data['name'],
                            "category_icon": category_data['icon']
                        })

                except Exception as e:
                    logger.error(f"Error processing {target} analyses: {str(e)}")
                    continue

            # Sort and paginate results
            all_results.sort(key=lambda x: x['created_at'], reverse=True)
            
            total_count = len(all_results)
            total_pages = (total_count + per_page - 1) // per_page

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_results = all_results[start_idx:end_idx]

            # Update response with consistent format
            response.update({
                "data": paginated_results,
                "meta": {
                    "page": page,
                    "per_page": per_page,
                    "total_items": total_count,
                    "total_pages": total_pages
                },
                "success": True
            })

            return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in get_analyses: {str(e)}", exc_info=True)
        return jsonify({
            **response,
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500


@analysis_bp.route('/analysis/generate-image', methods=['POST'])
def generate_analysis_image():
    """
    Generate an image based on analysis content using DALL-E.
    Returns a temporary URL from OpenAI.
    
    Request Body (form-data):
        content (str): The analysis content to use as context for image generation
        
    Returns:
        JSON: {
            "data": {
                "temp_image_url": str,  # Temporary URL from OpenAI
            } or None,
            "error": str or None,
            "success": bool,
            "message": str
        }
    """
    logger.info("Starting image generation process")
    response = {"data": None, "error": None, "success": False}
    
    try:
        # 1. Validate input content
        content = request.form.get('content')
        if not content:
            raise ValueError("Content is required")

        # 2. Validate content format
        title_end_index = content.find('<br>')
        if title_end_index == -1:
            raise ValueError("No newline found in the content, please add a space after the title")
        
        # 3. Extract content body
        content_body = content[title_end_index + 4:].strip()
        
        if not content_body:
            raise ValueError("Content body is empty")
        
        # 4. Generate image using DALL-E
        logger.info("Initializing image generation with DALL-E")
        image_generator = ImageGenerator()
        
        try:
            temp_image_url = image_generator.generate_image(content_body)
            if not temp_image_url:
                raise ValueError("Failed to generate image with DALL-E")
            
            logger.info(f"DALL-E image generated successfully: {temp_image_url}")
        except Exception as e:
            raise ValueError(f"Image generation failed: {str(e)}")

        return jsonify({
            "data": {
                "temp_image_url": temp_image_url
            },
            "message": "Image generated successfully",
            "success": True
        }), 201

    except ValueError as e:
        logger.error(f"Validation error in generate_analysis_image: {str(e)}")
        return jsonify({
            **response,
            "error": str(e),
            "message": "Image generation failed"
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_analysis_image: {str(e)}", exc_info=True)
        return jsonify({
            **response,
            "error": f"An unexpected error occurred: {str(e)}",
            "message": "Internal server error during image generation"
        }), 500

# Define a mapping between targets and their corresponding models
MODEL_MAPPING = {
    'deep_dive':  Analysis,         
    'daily_macro': DailyMacroAnalysis,
    'narratives': NarrativeTrading,
    'spotlight': SpotlightAnalysis,
    'support_resistance': SAndRAnalysis
}


def publish_analysis(coin_id: int, content: str, category_name: str, section_id: str, image_url: str) -> dict:
    """
    Publish an analysis with an image.
    
    Args:
        coin_id (int): The ID of the coin
        content (str): The analysis content
        category_name (str): The category name
        section_id (str): The section ID
        image_url (str): Either a temporary DALL-E URL or permanent S3 URL
    """
    logger.info(f"Starting publish_analysis for coin_id: {coin_id}, category: {category_name}, section_id: {section_id}")

    with Session() as session:
        try:
            # 1. Initial validations
            section = session.query(Sections).filter(Sections.id == section_id).first()
            if not section:
                logger.error(f"Section validation failed - no section found with id {section_id}")
                raise ValueError(f"No Section found with id {section_id}")
            
            target = section.target.lower()
            model_class = MODEL_MAPPING.get(target)

            if not model_class:
                logger.error(f"Model validation failed - invalid target type: {target}")
                raise ValueError(f"Invalid target type: {target}")

            category = session.query(Category).filter(Category.name.ilike(category_name)).first()
            if not category:
                logger.error(f"Category validation failed - no category found with name {category_name}")
                raise ValueError(f"No category found with name {category_name}")

            valid_starts = ('http://', 'https://')
            if not image_url.startswith(valid_starts):
                logger.error(f"Image URL validation failed - invalid format: {image_url}")
                raise ValueError(f"Invalid image URL format: {image_url}")
            
            # 2. Validate coin and get symbol
            coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()
            if not coin_bot:
                logger.error(f"Coin validation failed - no coin found with id {coin_id}")
                raise ValueError(f"No coin found with id {coin_id}")
            
            # 3. Process title for image filename
            title_end_index = content.find('<br>')
            if title_end_index == -1:
                logger.error("Title processing failed - no <br> separator found in content")
                raise ValueError("No newline found in the content, please add a space after the title")
            
            title = content[:title_end_index].strip()
            title = BeautifulSoup(title, 'html.parser').get_text()
            formatted_title = title.replace(':', '').replace(' ', '-').strip().lower()
            
            # 4. Process image if it's a temporary URL
            permanent_image_url = image_url
            if not 'appanalysisimages.s3' in image_url:
                try:
                    logger.info(f"Processing temporary DALL-E image: {image_url}")
                    image_filename = f"{formatted_title}.jpg"
                    
                    image_processor = ImageProcessor()
                    permanent_image_url = image_processor.process_and_upload_image(
                        image_url=image_url,
                        bucket_name='appanalysisimages',
                        image_filename=image_filename
                    )
                    
                    if not permanent_image_url:
                        logger.error("Failed to get permanent URL from S3 upload")
                        raise ValueError("Failed to process and upload image to S3")
                    
                except Exception as e:
                    logger.error(f"Image processing failed with error: {str(e)}", exc_info=True)
                    raise ValueError(f"Image processing failed: {str(e)}")

            coin_name = coin_bot.name
            
            # 5. Validate notification topics exist
            found_topics = notification_service.validate_topics(coin_name, target)
            if not found_topics:
                logger.error(f"No notification topics found for coin {coin_name} and type {target}")
                raise ValueError(f"No notification topics found for coin {coin_name} and type {target}")
            
            # 6. Create and save content with permanent image URL
            new_content = model_class.create_entry(content, permanent_image_url, category_name, coin_id)
            session.add(new_content)
            session.commit()
            session.refresh(new_content)

            # 7. Handle notifications
            notification_data = {
                "coin": coin_name,
                "title": f"{str(coin_name).upper()} New {section.name} Available",
                "body": f"{title} - Check it out!",
                "type": target,
                "timeframe": ""
            }
            
            emit_notification(event_name="new_analysis", data=notification_data)

            notification_service.push_notification(
                coin=coin_name,
                title=notification_data["title"],
                body=notification_data["body"],
                type=target,
                timeframe=""
            )

            return create_response(
                data=new_content.to_dict(),
                message=f"{section.name} published successfully",
                success=True,
            )

        except ValueError as e:
            session.rollback()
            logger.error(f"Validation error in publish_analysis: {str(e)}")
            return create_response(
                data=None,
                message=str(e),
                success=False,
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error in publish_analysis: {str(e)}", exc_info=True)
            return create_response(
                data=None,
                message=f"An unexpected error occurred: {str(e)}",
                success=False,
            )

# ____________________________________ Scheduled Analysis Endpoints __________________________________________________________
        

@analysis_bp.route('/scheduled-analyses', methods=['POST'])
def schedule_post() -> Tuple[Dict, int]:
    """
    Schedule a post for future publication.
    
    Expected form data:
       coin_id (int): The ID of the coin bot
       category_name (str): The name of the category
       content (str): The content of the post
       section_id(int): The ID of section
       temp_image_url (str): The temporary URL from DALL-E image generation
       scheduled_date (str): UTC datetime in ISO 8601 format
           Examples:
           - "2024-03-28T15:30:00.000Z"
           - "2024-03-28T15:30:00Z"
    """
    response = {"message": None, "error": None, "success": False, "job_id": None}
    
    try:
        with Session() as session:
            # 1. Extract and validate required fields
            required_fields = ['coin_id', 'category_name', 'content', 'scheduled_date', 'section_id', 'image_url']
            missing = [field for field in required_fields if not request.form.get(field)]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            # 2. Validate section exists
            section = session.query(Sections).filter(Sections.id == request.form['section_id']).first()
            if not section:
                raise ValueError(f"No Section found with id {request.form['section_id']}")

            # 3. Validate category exists
            category = session.query(Category).filter(Category.name.ilike(request.form['category_name'])).first()
            if not category:
                raise ValueError(f"No category found with name {request.form['category_name']}")

            # 4. Validate image URL format
            image_url = request.form['image_url']
            valid_starts = ('http://', 'https://')
            if not image_url.startswith(valid_starts):
                raise ValueError(f"Invalid image URL format: {image_url}")

            # 5. Validate coin exists
            try:
                coin_id = int(request.form['coin_id'])
            except ValueError:
                raise ValueError("coin_id must be a valid integer")

            coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()
            if not coin_bot:
                raise ValueError(f"No coin found with id {coin_id}")

            # 6. Validate content format
            content = request.form['content']
            title_end_index = content.find('<br>')
            if title_end_index == -1:
                raise ValueError("No newline found in the content, please add a space after the title")

            # 7. Parse and validate scheduled date
            scheduled_date = request.form['scheduled_date']
            try:
                # Try parsing with milliseconds
                scheduled_datetime = datetime.strptime(scheduled_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                try:
                    # Try parsing without milliseconds
                    scheduled_datetime = datetime.strptime(scheduled_date, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    raise ValueError("Invalid date format. Expected ISO 8601 format (e.g., '2024-03-28T15:30:00.000Z')")

            scheduled_datetime = pytz.utc.localize(scheduled_datetime).astimezone(chosen_timezone)
            
            if scheduled_datetime <= datetime.now(chosen_timezone):
                raise ValueError("Scheduled date must be in the future")

            # 8. Process and upload the temporary image to S3 immediately
            try:
                logger.info("Processing and uploading temporary image to S3")
                title = content[:title_end_index].strip()
                title = BeautifulSoup(title, 'html.parser').get_text()
                formatted_title = title.replace(':', '').replace(' ', '-').strip().lower()
                image_filename = f"{formatted_title}.jpg"
                
                image_processor = ImageProcessor()
                permanent_image_url = image_processor.process_and_upload_image(
                    image_url=image_url,
                    bucket_name='appanalysisimages',
                    image_filename=image_filename
                )
                
                if not permanent_image_url:
                    raise ValueError("Failed to process and upload image to S3")
                
                logger.info(f"Image processed and uploaded successfully: {permanent_image_url}")
            except Exception as e:
                raise ValueError(f"Image processing failed: {str(e)}")

            # 9. Validate notification topics exist
            target = section.target.lower()
            found_topics = notification_service.validate_topics(coin_bot.name, target)
            if not found_topics:
                raise ValueError(f"No notification topics found for coin {coin_bot.name} and type {target}")

            # 10. Schedule the job with permanent S3 URL
            job = sched.add_job(
                publish_analysis,
                args=[
                    coin_id,
                    content,
                    request.form['category_name'],
                    request.form['section_id'],
                    permanent_image_url  # Use permanent S3 URL instead of temporary URL
                ],
                trigger=DateTrigger(run_date=scheduled_datetime)
            )

            return jsonify({
                "message": "Post scheduled successfully",
                "success": True,
                "job_id": job.id,
                "scheduled_time": scheduled_datetime.isoformat()
            }), 201

    except ValueError as e:
        logger.error(f"Validation error in schedule_post: {str(e)}")
        return jsonify({
            **response,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error in schedule_post: {str(e)}")
        return jsonify({
            **response,
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500


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
    Get detailed information about a scheduled job by its ID.

    Args:
        job_id (str): The ID of the scheduled job to retrieve.

    Returns:
        JSON: {
            "data": {
                "id": str,
                "coin_id": int,
                "coin_name": str,
                "coin_icon": str,
                "section_name": str,
                "section_id": str,
                "title": str,
                "content": str,
                "image_url": str,
                "scheduled_time": str,
                "category_name": str
            } or None,
            "error": str or None,
            "success": bool
        }
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 500  # Default to server error
    
    try:
        job = sched.get_job(job_id)
        
        if job is None:
            response["error"] = "Scheduled job not found"
            status_code = 404
        else:
            with Session() as session:
                if job.name == 'publish_analysis':
                    # Extract arguments from the job
                    coin_id, content, category_name, section_id, image_url = job.args

                    # Get coin information
                    coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()

                    # Get category information including icon
                    category = session.query(Category).filter(Category.name.ilike(category_name)).first()
                    
                    # Get section information
                    section = session.query(Sections).filter(Sections.id == section_id).first()

                    # Extract title from content
                    title_end_index = content.find('<br>')
                    title = content[:title_end_index].strip() if title_end_index != -1 else ""
                    content_body = content[title_end_index + 4:].strip() if title_end_index != -1 else content

                    # Clean title from HTML tags
                    title = BeautifulSoup(title, 'html.parser').get_text()

                    response["data"] = {
                        "id": job.id,
                        "coin_id": coin_id,
                        "coin_name": coin_bot.name if coin_bot else "",
                        "coin_icon": coin_bot.icon if coin_bot else "",
                        "section_name": section.name if section else "",
                        "section_id": section_id,
                        "title": title,
                        "content": content_body,
                        "image_url": image_url,
                        "scheduled_time": job.next_run_time.isoformat(),
                        "category_name": category.name if category else "",
                        "category_icon": category.icon if category else ""
                    }
                    response["success"] = True
                    status_code = 200
                else:
                    response["error"] = "Invalid job type"
                    status_code = 400

    except Exception as e:
        logger.error(f"Error fetching scheduled job {job_id}: {str(e)}")
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    
    return jsonify(response), status_code


@analysis_bp.route('/scheduled-analyses', methods=['GET'])
def get_scheduled_analyses():
    """
    Get all scheduled analyses with formatted data for card rendering.
    Supports filtering by timeframe: today, this week, this month
    
    Query Parameters:
        timeframe (str): Optional filter - 'today', 'week', 'month'
    
    Returns:
        JSON: {
            "data": {
                "jobs": [
                    {
                        "id": str,
                        "coin_id": int,
                        "coin_name": str,
                        "coin_icon": str,
                        "section_name": str,
                        "section_id": str,
                        "title": str,
                        "content": str,
                        "image_url": str,
                        "scheduled_time": str,
                        "category_name": str,
                        "category_icon": str
                    }
                ]
            },
            "error": str or None,
            "success": bool
        }
    """
    try:
        timeframe = request.args.get('timeframe', '').lower()
        now = datetime.now(chosen_timezone)
        
        # Define timeframe filters
        if timeframe == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif timeframe == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        elif timeframe == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=32)).replace(day=1)
        else:
            # If no timeframe specified, get all future jobs
            start_date = now
            end_date = now.replace(year=now.year + 10)  # 10 years in the future

        scheduled_jobs = sched.get_jobs()
        formatted_jobs = []

        with Session() as session:
            for job in scheduled_jobs:
                if job.name == 'publish_analysis':
                    job_time = job.next_run_time.astimezone(chosen_timezone)
                    
                    # Skip if job is outside the selected timeframe
                    if not (start_date <= job_time < end_date):
                        continue

                    # Extract arguments from the job
                    coin_id, content, category_name, section_id, image_url = job.args

                    # Get coin information
                    coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()
                    
                    # Get section information
                    section = session.query(Sections).filter(Sections.id == section_id).first()

                    # Get category information including icon
                    category = session.query(Category).filter(Category.name.ilike(category_name)).first()

                    # Extract title from content
                    title_end_index = content.find('<br>')
                    title = content[:title_end_index].strip() if title_end_index != -1 else ""
                    content_body = content[title_end_index + 4:].strip() if title_end_index != -1 else content

                    # Clean title from HTML tags
                    title = BeautifulSoup(title, 'html.parser').get_text()

                    formatted_job = {
                        "id": job.id,
                        "coin_id": coin_id,
                        "coin_name": coin_bot.name if coin_bot else "",
                        "coin_icon": coin_bot.icon if coin_bot else "",
                        "section_name": section.name if section else "",
                        "section_id": section_id,
                        "title": title,
                        "content": content_body,
                        "image_url": image_url,
                        "scheduled_time": job_time.isoformat(),
                        "category_name": category_name,
                        "category_icon": category.icon if category else None
                    }
                    formatted_jobs.append(formatted_job)

        # Sort jobs by scheduled time
        formatted_jobs.sort(key=lambda x: x['scheduled_time'])

        return jsonify({
            "data": {
                "jobs": formatted_jobs
            },
            "error": None,
            "success": True
        }), 200

    except Exception as e:
        logger.error(f"Error fetching scheduled analyses: {str(e)}")
        return jsonify({
            "data": {"jobs": []},
            "error": f"An error occurred while fetching scheduled analyses: {str(e)}",
            "success": False
        }), 500

