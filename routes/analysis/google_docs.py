from flask import Blueprint, request
import base64
from config import Analysis, AnalysisImage, Session

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis', methods=['POST'])
def get_data_from_apis():
    try:
        coin_bot = request.form.get('coinBot')
        content = request.form.get('content')
        image_data = request.form.get('image')
        id = request.form.get('id') 
        image_bytes = base64.b64decode(image_data)

        print(f'Title: {coin_bot}')
        print(f'ID: {id}')  # Print the 'id'
        print(f'Image saved as {coin_bot}.png')
        print(f'content: {content}')

        with Session() as session:
            new_analysis = Analysis(
                analysis=content,
                coin_bot_id=id
            )
            session.add(new_analysis)
            session.commit()

            new_analysis_image = AnalysisImage(
                image=image_bytes,
                analysis_id=new_analysis.analysis_id,
            )
            session.add(new_analysis_image)
            session.commit()

        return 'Analysis sent successfully', 200

    except Exception as e:
        print(f'Error found: {str(e)}')
        return f'Error found: {str(e)}', 500


# # from PIL import Image
# from io import BytesIO
        # image = Image.open(BytesIO(image_bytes))

        # image.save(f'{coin_bot}.png', 'PNG')