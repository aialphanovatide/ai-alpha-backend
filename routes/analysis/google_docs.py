from flask import Blueprint, request
import base64
# from PIL import Image
from io import BytesIO

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis', methods=['POST'])
def get_data_from_apis():
    try:
        coin_bot = request.form.get('coinBot')
        content = request.form.get('content')
        image_data = request.form.get('image')

        image_bytes = base64.b64decode(image_data)

        # image = Image.open(BytesIO(image_bytes))

        # image.save(f'{coin_bot}.png', 'PNG')

        print(f'Title: {coin_bot}')
        print(f'Image saved as {coin_bot}.png')
        print(f'content: {content}')


        return 'Analysis sent successfully', 200
    
    except Exception as e:
        return f'Error found: {str(e)}', 500