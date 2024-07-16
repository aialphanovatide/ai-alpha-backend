import os
import boto3
import datetime
import requests
from PIL import Image
from io import BytesIO
from sqlalchemy import desc
from datetime import datetime
from dotenv import load_dotenv
from typing import Tuple, Optional, Dict
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm.exc import NoResultFound
from apscheduler.jobstores.base import JobLookupError
from botocore.exceptions import ClientError, BotoCoreError
from config import Analysis, AnalysisImage, session, CoinBot, Session
from apscheduler.schedulers.background import BackgroundScheduler
from routes.news_bot.poster_generator import generate_poster_prompt

sched = BackgroundScheduler()
if sched.state != 1:
    sched.start()
    print("--- Second Scheduler started ----")

analysis_bp = Blueprint('analysis_bp', __name__)

load_dotenv()

AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')

# THIS FUNCTION SEEMS TO BE DUPLICATED WITH THE ONE ON routes/news_bot/poster_generator
# Verify and remove if it is.
def resize_and_upload_image_to_s3(
    image_data: str,
    bucket_name: str,
    image_filename: str,
    target_size: Tuple[int, int] = (256, 256),
    region_name: str = 'us-east-2',
    aws_access_key_id: str = AWS_ACCESS,
    aws_secret_access_key: str = AWS_SECRET_KEY
) -> Optional[str]:
    """
    Resize an image from a URL and upload it to an S3 bucket.

    Args:
        image_data (str): URL of the image to be resized and uploaded.
        bucket_name (str): Name of the S3 bucket to upload to.
        image_filename (str): Desired filename for the uploaded image.
        target_size (Tuple[int, int]): Desired dimensions for the resized image. Default is (256, 256).
        region_name (str): AWS region name. Default is 'us-east-2'.
        aws_access_key_id (str): AWS access key ID.
        aws_secret_access_key (str): AWS secret access key.

    Returns:
        Optional[str]: URL of the uploaded image in S3, or None if an error occurred.
    """
    try:
        # Fetch the image from the URL
        response = requests.get(image_data, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Open the image using PIL
        image = Image.open(BytesIO(response.content))

        # Resize the image
        resized_image = image.resize(target_size)

        # Prepare S3 client
        s3 = boto3.client(
            's3',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        # Upload the resized image to S3
        with BytesIO() as output:
            resized_image.save(output, format="JPEG")
            output.seek(0)
            s3.upload_fileobj(output, bucket_name, image_filename)

        # Generate and return the URL of the uploaded image
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{image_filename}"
        return image_url

    except requests.RequestException as e:
        print(f"Error fetching image: {str(e)}")
    except IOError as e:
        print(f"Error processing image: {str(e)}")
    except (BotoCoreError, ClientError) as e:
        print(f"Error uploading to S3: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

    return None


# @analysis_bp.route('/get_analysis/<int:coin_bot_id>', methods=['GET'])
# def get_analysis(coin_bot_id):

#     try:
#         analysis_objects = session.query(Analysis).filter_by(
#             coin_bot_id=coin_bot_id).order_by(desc(Analysis.created_at)).all()
#         analysis_data = []

#         # Iterates over the analysis dict and gets the images related to each analysis
#         for analy in analysis_objects:
#             analysis_dict = analy.to_dict()

#             images_objects = session.query(AnalysisImage).filter_by(
#                 analysis_id=analy.analysis_id).all()
#             images_data = [{'image_id': img.image_id, 'image': img.image}
#                            for img in images_objects]

#             analysis_dict['analysis_images'] = images_data
#             analysis_data.append(analysis_dict)

#         # TO CHECK THE DATA IN analysis_data
#         # for analy in analysis_data:
#         #     print(f"Analysis ID: {analy['analysis_id']}, Analysis: {analy['analysis']}, Created At: {analy['created_at']}")
#         #     for img in analy['analysis_images']:
#         #         print(f"  Image ID: {img['image_id']}, Image: {img['image']}")

#         return jsonify({'message': analysis_data, 'success': True, 'status': 200}), 200

#     except Exception as e:
#         session.rollback()
#         return jsonify({'message': str(e), 'success': False, 'status': 500}), 500
#   # Gets all the analysis related to a coin

# # Fn to get analysis related to a coin id


# def get_analysis_by_id(coin_bot_id):
#     return session.query(Analysis).filter_by(coin_bot_id=coin_bot_id).order_by(desc(Analysis.created_at)).all()

# # Fn to get Analysis related to a coin name


# def get_analysis_by_name(coin_bot_name):
#     coin = session.query(CoinBot).filter(
#         CoinBot.bot_name == coin_bot_name).first()
#     return session.query(Analysis).filter_by(coin_bot_id=coin.bot_id).all() if coin else None

# # fn to get analysis images


# def get_analysis_images(analysis_object):
#     return [{'image_id': img.image_id, 'image': img.image} for img in session.query(AnalysisImage).filter_by(analysis_id=analysis_object.analysis_id).all()]

# # Route to get analysis by coin id/name
# @analysis_bp.route('/api/get_analysis_by_coin', methods=['GET'])
# def get_analysis_by_coin():
#     try:
#         coin_bot_name = request.args.get('coin_bot_name')
#         coin_bot_id = request.args.get('coin_bot_id')

#         if not coin_bot_id and not coin_bot_name:
#             return jsonify({'message': 'Coin ID or name is missing', 'status': 400}), 400

#         analysis_objects = []
#         if coin_bot_name:
#             analysis_objects = get_analysis_by_name(coin_bot_name)
#         elif coin_bot_id:
#             analysis_objects = get_analysis_by_id(coin_bot_id)

#         if not analysis_objects:
#             return jsonify({'message': 'No analysis found', 'status': 404}), 404

#         analysis_data = [{'analysis': analy.to_dict(
#         ), 'analysis_images': get_analysis_images(analy)} for analy in analysis_objects]

#         return jsonify({'message': analysis_data, 'success': True, 'status': 200}), 200

#     except Exception as e:
#         session.rollback()
#         return jsonify({'message': str(e), 'success': False, 'status': 500}), 500


# # Gets all the analysis from all coins
# @analysis_bp.route('/get_analysis', methods=['GET'])
# def get_all_analysis():

#     try:
#         analysis_objects = session.query(Analysis).order_by(
#             desc(Analysis.created_at)).all()
#         analysis_data = []

#         # Iterates over the analysis dict and gets the images related to each analysis
#         for analy in analysis_objects:
#             analysis_dict = analy.to_dict()

#             images_objects = session.query(AnalysisImage).filter_by(
#                 analysis_id=analy.analysis_id).all()
#             images_data = [{'image_id': img.image_id, 'image': img.image}
#                            for img in images_objects]
            
#             analysis_dict['category_name'] = analy.category_name
#             analysis_dict['analysis_images'] = images_data
#             analysis_dict['coin_bot_id'] = analy.coin_bot_id
#             analysis_data.append(analysis_dict)

#         return jsonify({'message': analysis_data, 'success': True, 'status': 200}), 200

#     except Exception as e:
#         session.rollback()
#         return jsonify({'message': str(e), 'success': False, 'status': 500}), 500


# # Creates an analysis
# @analysis_bp.route('/post_analysis', methods=['POST'])
# def post_analysis():
#     try:
#         coin_bot_id = request.form.get('coinBot')
#         content = request.form.get('content')
#         category_name = request.form.get('category_name')
#         # image_file = request.files.get('image')

#         # Check if any of the required values is missing
#         if content == 'null' or coin_bot_id == 'null':
#             return jsonify({'error': 'One or more required values are missing', 'status': 400, 'success': False}), 400
        
#         if category_name == 'null' or coin_bot_id == 'null':
#             return jsonify({'error': 'One or more required values are missing', 'status': 400, 'success': False}), 400

#         # Check if any of the required values is missing
#         if coin_bot_id is None or not coin_bot_id or content is None or not content:
#             return jsonify({'error': 'One or more required values are missing', 'status': 400, 'success': False}), 400
        
        

#         new_analysis = Analysis(
#             analysis=content,
#             coin_bot_id=coin_bot_id,
#             category_name=category_name
#         )
        
#         session.add(new_analysis)
#         session.commit()
        
#         if new_analysis:
#             image = generate_poster_prompt(new_analysis.analysis)
#             print("image generated")
#             analysis_id = new_analysis.analysis_id
#             print('id analysis', analysis_id)
#             image_filename = f"{analysis_id}.jpg"    
#             print('filename: ', image_filename)
#             if image:
#                     try:
#                                 # Resize and upload the image to S3
#                         resized_image_url = resize_and_upload_image_to_s3(image, 'appanalysisimages', image_filename)

#                         if resized_image_url:
#                              print("Image resized and uploaded to S3 successfully.")
#                         else:
#                              print("Error resizing and uploading the image to S3.")
#                     except Exception as e:
#                         print("Error:", e)
#             else:
#                 print("Image not generated.")
        
        


#         # Return success response if everything is fine
#         return jsonify({'message': 'Analysis posted successfully', 'status': 200, 'success': True}), 200
#     except Exception as e:
#         session.rollback()
#         return jsonify({'error': str(e), 'status': 500, 'success': False}), 500


# # Deletes an analysis passing the analysis_id
# @analysis_bp.route('/delete_analysis/<int:analysis_id>', methods=['DELETE'])
# def delete_analysis(analysis_id):
#     try:
#         # Check if the analysis_id exists
#         analysis_to_delete = session.query(Analysis).filter(
#             Analysis.analysis_id == analysis_id).first()
#         if analysis_to_delete is None:
#             return jsonify({'error': 'Analysis not found', 'status': 404, 'success': False}), 404

#         # Delete the associated image if it exists
#         analysis_image_to_delete = session.query(
#             AnalysisImage).filter_by(analysis_id=analysis_id).first()

#         if analysis_image_to_delete:
#             session.delete(analysis_image_to_delete)

#         # Delete the analysis
#         session.delete(analysis_to_delete)
#         session.commit()

#         return jsonify({'message': 'Analysis deleted successfully', 'status': 200, 'success': True}), 200

#     except Exception as e:
#         session.rollback()
#         return jsonify({'error': str(e), 'status': 500, 'success': False}), 500

# # Edits an analysis
# @analysis_bp.route('/edit_analysis/<int:analysis_id>', methods=['PUT'])
# def edit_analysis(analysis_id):
#     try:
#         # Check if the analysis_id exists
#         analysis_to_edit = session.query(Analysis).filter(
#             Analysis.analysis_id == analysis_id).first()
#         if analysis_to_edit is None:
#             return jsonify({'error': 'Analysis not found', 'status': 404, 'success': False}), 404

#         # Update analysis content if provided
#         new_content = request.json.get('content')

#         if not new_content:
#             return jsonify({'error': 'New content is required to edit the Analysis', 'status': 400, 'success': False}), 400

#         analysis_to_edit.analysis = new_content
#         session.commit()

#         return jsonify({'message': 'Analysis edited successfully', 'status': 200, 'success': True}), 200

#     except Exception as e:
#         session.rollback()
#         return jsonify({'error': str(e), 'status': 500, 'success': False}), 500


# # Gets the name and date of the last analysis created
# @analysis_bp.route('/get_last_analysis', methods=['GET'])
# def get_last_analysis():
#     try:
#         # Retrieve the last analysis created
#         last_analysis = session.query(Analysis).order_by(
#             Analysis.created_at.desc()).first()

#         if last_analysis is None:
#             return jsonify({'error': 'No analysis found', 'status': 404, 'success': False}), 404

#         coin = session.query(CoinBot).filter(
#             CoinBot.bot_id == last_analysis.coin_bot_id).first()

#         # Extract relevant information, such as analysis content and creation date
#         analysis_data = {
#             'analysis_id': last_analysis.analysis_id,
#             'content': last_analysis.analysis,
#             'coin_name': coin.bot_name,
#             'category_name': last_analysis.category_name,
#             'created_at': last_analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
#         }

#         return jsonify({'last_analysis': analysis_data, 'status': 200, 'success': True}), 200

#     except Exception as e:
#         session.rollback()
#         return jsonify({'error': str(e), 'status': 500, 'success': False}), 500


# # Funtion to execute by the scheduler
# def publish_analysis(coin_bot_id, content, category_name):
#     title_end_index = content.find('\n')
#     if title_end_index != -1:
#         # Extract title and remove leading/trailing spaces
#         title = content[:title_end_index].strip()
#         # Extract content after the title
#         content = content[title_end_index+1:]
#     else:
#         title = ''  # If no newline found, set title to empty string
#     # Create new analysis instance
#     new_analysis = Analysis(analysis=content, category_name=category_name, coin_bot_id=coin_bot_id)
#     session.add(new_analysis)
#     session.commit()
#     print("Publishing analysis with title:", title)


# @analysis_bp.route('/schedule_post', methods=['POST'])
# def schedule_post():
#     try:
#         if not sched.running:
#             sched.start()

#         coin_bot_id = request.form.get('coinBot')
#         category_name = request.form.get('category_name')
#         content = request.form.get('content')
#         scheduled_date_str = request.form.get('scheduledDate')

#         if not (coin_bot_id and content and scheduled_date_str):
#             return jsonify({'error': 'One or more required values are missing', 'status': 400, 'success': False}), 400

#         # Crear un objeto datetime
#         scheduled_datetime = datetime.strptime(
#             scheduled_date_str, '%a, %b %d, %Y, %I:%M:%S %p')

#         # Agregar un nuevo trabajo
#         sched.add_job(publish_analysis, args=[coin_bot_id, content, category_name], trigger=DateTrigger(run_date=scheduled_datetime))

#         return jsonify({'message': 'Post scheduled successfully', 'status': 200, 'success': True}), 200
#     except Exception as e:
#         return jsonify({'error': str(e), 'status': 500, 'success': False}), 500





# # Deletes a scheduled job by job id
# @analysis_bp.route('/delete_scheduled_job/<string:job_id>', methods=['DELETE'])
# def delete_scheduled_job(job_id):
#     try:
#         # Find the by schedule analysis by ID
#         job = sched.get_job(job_id)
#         if job is None:
#             return jsonify({'error': 'Scheduled job not found', 'status': 404, 'success': False}), 404

#         # Deletes an analysis
#         sched.remove_job(job_id)

#         return jsonify({'message': 'Scheduled job deleted successfully', 'status': 200, 'success': True}), 200

#     except JobLookupError as e:
#         return jsonify({'error': str(e), 'status': 404, 'success': False}), 404
#     except Exception as e:
#         return jsonify({'error': str(e), 'status': 500, 'success': False}), 500
    

# ____________ THIS SHOULD THE THE STRUCTURE OF THE ROUTES _____________________

# Key Improvements:
    # Session Management
    # Code Structure
    # Docstring Details
    # Consistant response Format
    # Error handling

@analysis_bp.route('/get_analysis/<int:coin_bot_id>', methods=['GET'])
def get_analysis(coin_bot_id):
    """
    Retrieve analyses for a specific coin bot ID with pagination.

    This endpoint queries the database for analyses related to a specific coin bot,
    ordered by creation date descending, and includes their associated images.

    Args:
        coin_bot_id (int): The ID of the coin bot
        page (int): The page number (default: 1)
        limit (int): The number of items per page (default: 10, max: 100)

    Returns:
        JSON: A JSON object containing:
            - data (list): List of analysis objects with their associated images
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
            - total (int): Total number of analyses for this coin bot
            - page (int): Current page number
            - limit (int): Number of items per page
            - total_pages (int): Total number of pages
        HTTP Status Code

    Raises:
        400 Bad Request: If invalid pagination parameters are provided
        404 Not Found: If no analyses are found for the specified coin bot ID
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

    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 10, type=int), 100)  # Cap at 100

        if page < 1 or limit < 1:
            response["error"] = "Invalid pagination parameters"
            status_code = 400
            return jsonify(response), status_code

        with Session() as session:
            # Get total count
            total_analyses = session.query(Analysis).filter(Analysis.coin_bot_id == coin_bot_id).count()

            if total_analyses == 0:
                response["error"] = f"No analyses found for coin bot ID: {coin_bot_id}"
                status_code = 404
                return jsonify(response), status_code

            # Calculate pagination values
            total_pages = (total_analyses + limit - 1) // limit
            offset = (page - 1) * limit

            # Query for analyses and their associated images with pagination
            analysis_query = session.query(Analysis, AnalysisImage)\
                .outerjoin(AnalysisImage, Analysis.analysis_id == AnalysisImage.analysis_id)\
                .filter(Analysis.coin_bot_id == coin_bot_id)\
                .order_by(desc(Analysis.created_at))\
                .offset(offset)\
                .limit(limit)

            analysis_data = {}
            for analysis, image in analysis_query:
                if analysis.analysis_id not in analysis_data:
                    analysis_dict = analysis.to_dict()
                    analysis_dict['analysis_images'] = []
                    analysis_data[analysis.analysis_id] = analysis_dict
                
                if image:
                    analysis_data[analysis.analysis_id]['analysis_images'].append({
                        'image_id': image.image_id,
                        'image': image.image
                    })

            response["data"] = list(analysis_data.values())
            response["success"] = True
            response["total"] = total_analyses
            response["page"] = page
            response["limit"] = limit
            response["total_pages"] = total_pages
            status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@analysis_bp.route('/get_analysis_by_coin', methods=['GET'])
def get_analysis_by_coin():
    """
    Retrieve analyses for a specific coin by name or ID.

    This endpoint queries the database for analyses related to a specific coin,
    identified either by name or ID.

    Args:
        coin_bot_name (str): The name of the coin (optional)
        coin_bot_id (str): The ID of the coin (optional)

    Returns:
        JSON: A JSON object containing:
            - data (list): List of analysis objects with their associated images
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If neither coin name nor ID is provided
        404 Not Found: If no analyses are found for the specified coin
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    try:
        coin_bot_name = request.args.get('coin_bot_name')
        coin_bot_id = request.args.get('coin_bot_id')

        if not coin_bot_id and not coin_bot_name:
            response["error"] = "Coin ID or name is required"
            status_code = 400
            return jsonify(response), status_code
        
        with Session() as session:
            # Query for analyses
            query = session.query(Analysis)
            if coin_bot_id:
                query = query.filter(Analysis.coin_bot_id == coin_bot_id)
            elif coin_bot_name:
                coin = session.query(CoinBot).filter(CoinBot.bot_name == coin_bot_name).first()
                if not coin:
                    response["error"] = f"No coin found with name: {coin_bot_name}"
                    status_code = 404
                    return jsonify(response), status_code
                query = query.filter(Analysis.coin_bot_id == coin.bot_id)

            analysis_objects = query.order_by(desc(Analysis.created_at)).all()

            if not analysis_objects:
                response["error"] = "No analysis found for the specified coin"
                status_code = 404
                return jsonify(response), status_code

            analysis_data = []
            for analy in analysis_objects:
                analysis_dict = analy.to_dict()
                
                # Get associated images
                images = session.query(AnalysisImage).filter_by(analysis_id=analy.analysis_id).all()
                images_data = [{'image_id': img.image_id, 'image': img.image} for img in images]
                
                analysis_dict['analysis_images'] = images_data
                analysis_data.append(analysis_dict)

            response["data"] = analysis_data
            response["success"] = True
            status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@analysis_bp.route('/get_analysis', methods=['GET'])
def get_all_analysis():
    """
    Retrieve analyses with their associated images, with pagination.

    This endpoint queries the database for analyses, ordered by creation date descending,
    and includes their associated images. It supports pagination and a configurable limit.

    Args:
        page (int): The page number (default: 1)
        limit (int): The number of items per page (default: 10, max: 100)

    Returns:
        JSON: A JSON object containing:
            - data (list): List of analysis objects with their associated images
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

    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 10, type=int), 100)  # Cap at 100

        if page < 1 or limit < 1:
            response["error"] = "Invalid pagination parameters"
            status_code = 400
            return jsonify(response), status_code
        
        with Session() as session:
            # Query for total count
            total_analyses = session.query(Analysis).count()

            # Calculate pagination values
            total_pages = (total_analyses + limit - 1) // limit
            offset = (page - 1) * limit

            # Query with pagination
            analysis_objects = session.query(Analysis).order_by(desc(Analysis.created_at)).offset(offset).limit(limit).all()

            analysis_data = []

            for analy in analysis_objects:
                analysis_dict = analy.to_dict()

                images_objects = session.query(AnalysisImage).filter_by(analysis_id=analy.analysis_id).all()
                images_data = [{'image_id': img.image_id, 'image': img.image} for img in images_objects]
                
                analysis_dict['category_name'] = analy.category_name
                analysis_dict['analysis_images'] = images_data
                analysis_dict['coin_bot_id'] = analy.coin_bot_id
                analysis_data.append(analysis_dict)

            response["data"] = analysis_data
            response["success"] = True
            response["total"] = total_analyses
            response["page"] = page
            response["limit"] = limit
            response["total_pages"] = total_pages
            status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@analysis_bp.route('/post_analysis', methods=['POST'])
def post_analysis():
    """
    Create a new analysis and generate an associated image.

    This endpoint creates a new analysis based on the provided data,
    generates an image for the analysis, and uploads it to S3.

    Args:
        None (data is expected in the request form)

    Returns:
        JSON: A JSON object containing:
            - data (dict or None): Details of the created analysis, if successful
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If required data is missing
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "data": None,
        "error": None,
        "success": False
    }
    status_code = 500  # Default to server error

    coin_bot_id = request.form.get('coinBot')
    content = request.form.get('content')
    category_name = request.form.get('category_name')
    # Check if any of the required values is missing or null
    if not coin_bot_id or coin_bot_id == 'null' or not content or content == 'null' or not category_name or category_name == 'null':
        response["error"] = "One or more required values are missing or null"
        return jsonify(response), 400

    session = Session()
    try:
        new_analysis = Analysis(
            analysis=content,
            coin_bot_id=coin_bot_id,
            category_name=category_name
        )
        
        session.add(new_analysis)
        session.flush()  # This will populate new_analysis.analysis_id

        # Generate and upload image
        image = generate_poster_prompt(new_analysis.analysis)
        if not image:
            raise ValueError("Image not generated")

        image_filename = f"{new_analysis.analysis_id}.jpg"
        resized_image_url = resize_and_upload_image_to_s3(image, 'appanalysisimages', image_filename)
        if not resized_image_url:
            raise ValueError("Error resizing and uploading the image to S3")

        session.commit()

        response["data"] = {
            "analysis_id": new_analysis.analysis_id,
            "content": new_analysis.analysis,
            "coin_bot_id": new_analysis.coin_bot_id,
            "category_name": new_analysis.category_name,
            "created_at": new_analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "image_url": resized_image_url
        }
        response["success"] = True
        status_code = 200

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except ValueError as e:
        session.rollback()
        response["error"] = str(e)
        status_code = 500
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code


@analysis_bp.route('/delete_analysis/<int:analysis_id>', methods=['DELETE'])
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

    try:
        # Check if the analysis_id exists
        analysis_to_delete = session.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
        if analysis_to_delete is None:
            response["error"] = "Analysis not found"
            status_code = 404
            return jsonify(response), status_code

        # Store some data about the analysis for the response
        deleted_analysis_data = {
            "analysis_id": analysis_to_delete.analysis_id,
            "created_at": analysis_to_delete.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "had_image": False
        }

        # Delete the associated image if it exists
        analysis_image_to_delete = session.query(AnalysisImage).filter_by(analysis_id=analysis_id).first()
        if analysis_image_to_delete:
            session.delete(analysis_image_to_delete)
            deleted_analysis_data["had_image"] = True

        # Delete the analysis
        session.delete(analysis_to_delete)
        session.commit()

        response["data"] = deleted_analysis_data
        response["success"] = True
        status_code = 200

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@analysis_bp.route('/edit_analysis/<int:analysis_id>', methods=['PUT'])
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
        return jsonify(response), 400

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
        response["data"] = {
            "analysis_id": analysis_to_edit.analysis_id,
            "content": analysis_to_edit.analysis,
            "updated_at": analysis_to_edit.updated_at.strftime('%Y-%m-%d %H:%M:%S') 
        }
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


@analysis_bp.route('/get_last_analysis', methods=['GET'])
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

        # Retrieve the associated coin
        try:
            coin = session.query(CoinBot).filter(CoinBot.bot_id == last_analysis.coin_bot_id).one()
        except NoResultFound:
            response["error"] = "Associated coin not found"
            status_code = 404
            return jsonify(response), status_code

        # Prepare the response data
        analysis_data = {
            'analysis_id': last_analysis.analysis_id,
            'content': last_analysis.analysis,
            'coin_name': coin.bot_name,
            'category_name': last_analysis.category_name,
            'created_at': last_analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        response["data"] = analysis_data
        response["success"] = True
        status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code
    

def publish_analysis(coin_bot_id: int, content: str, category_name: str) -> None:
    """
    Function to be executed by the scheduler to publish an analysis.

    Args:
        coin_bot_id (int): The ID of the coin bot
        content (str): The content of the analysis
        category_name (str): The name of the category

    Raises:
        SQLAlchemyError: If there's an error with the database operation
    """
    session = Session()
    try:
        title_end_index = content.find('\n')
        if title_end_index != -1:
            title = content[:title_end_index].strip()
            content = content[title_end_index+1:]
        else:
            title = ''

        new_analysis = Analysis(analysis=content, category_name=category_name, coin_bot_id=coin_bot_id)
        session.add(new_analysis)
        session.commit()
        print(f"Publishing analysis with title: {title}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error publishing analysis: {str(e)}")
    finally:
        session.close()

@analysis_bp.route('/schedule_post', methods=['POST'])
def schedule_post() -> Tuple[Dict, int]:
    """
    Schedule a post for future publication.

    Expected form data:
        coinBot (str): The ID of the coin bot
        category_name (str): The name of the category
        content (str): The content of the post
        scheduledDate (str): The scheduled date and time in the format 'Mon, Jan 01, 2023, 12:00:00 AM'

    Returns:
        JSON response with status code:
        - 200: Post scheduled successfully
        - 400: Bad request (missing or invalid data)
        - 500: Server error
    """
    response = {"message": None, "error": None, "success": False, "job_id": None}
    status_code = 500  # Default to server error

    try:
        coin_bot_id = request.form.get('coinBot')
        category_name = request.form.get('category_name')
        content = request.form.get('content')
        scheduled_date_str = request.form.get('scheduledDate')

        if not all([coin_bot_id, category_name, content, scheduled_date_str]):
            response["error"] = "One or more required values are missing"
            status_code = 400
            return jsonify(response), status_code

        try:
            coin_bot_id = int(coin_bot_id)
            scheduled_datetime = datetime.strptime(scheduled_date_str, '%a, %b %d, %Y, %I:%M:%S %p')
        except ValueError as e:
            response["error"] = f"Invalid input format: {str(e)}"
            status_code = 400
            return jsonify(response), status_code

        job = sched.add_job(
            publish_analysis, 
            args=[coin_bot_id, content, category_name], 
            trigger=DateTrigger(run_date=scheduled_datetime)
        )

        response["message"] = "Post scheduled successfully"
        response["job_id"] = job.id
        response["success"] = True
        status_code = 200

    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@analysis_bp.route('/delete_scheduled_job/<string:job_id>', methods=['DELETE'])
def delete_scheduled_job(job_id):
    """
    Delete a scheduled job by its ID.

    Args:
        job_id (str): The ID of the scheduled job to delete.

    Returns:
        JSON response with status code:
        - 200: Job deleted successfully
        - 404: Job not found
        - 500: Server error
    """
    response = {"message": None, "error": None, "job_id": job_id, "success": False}
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
            status_code = 200

    except JobLookupError as e:
        response["error"] = f"Error looking up job: {str(e)}"
        status_code = 404
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    
    return jsonify(response), status_code


@analysis_bp.route('/get_scheduled_job/<string:job_id>', methods=['GET'])
def get_scheduled_job(job_id):
    """
    Get information about a scheduled job by its ID.

    Args:
        job_id (str): The ID of the scheduled job to retrieve.

    Returns:
        JSON response with status code:
        - 200: Job information retrieved successfully
        - 404: Job not found
        - 500: Server error
    """
    response = {"data": None, "error": None, "job_id": job_id, "success": False}
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
            status_code = 200

    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    
    return jsonify(response), status_code


# Gets all the schedule analysis
@analysis_bp.route('/get_scheduled_jobs', methods=['GET'])
def get_jobs():
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

        return jsonify({'jobs': job_listing, 'status': 200, 'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 500, 'success': False}), 500