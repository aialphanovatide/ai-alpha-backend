from config import Analysis, AnalysisImage
from flask import request
from config import Session as DBSession 
from flask import Blueprint

post_new_analysis = Blueprint('postNewAnalysis', __name__)

#route to post analysis
@post_new_analysis.route('/post_analysis', methods=['POST'])
def post_analysis():
    try:
        coin_bot_id = request.form.get('coinBot')
        content = request.form.get('content')
        image_file = request.files.get('image')

        print(f'Coin Bot ID: {coin_bot_id}')
        print(f'Content: {content}')

        with DBSession() as db_session:
            new_analysis = Analysis(
                analysis=content,
                coin_bot_id=coin_bot_id 
            )
            db_session.add(new_analysis)
            db_session.commit()

            if image_file:
                image_data = image_file.read()
                new_analysis_image = AnalysisImage(
                    image=image_data,
                    analysis_id=new_analysis.analysis_id,
                )
                db_session.add(new_analysis_image)
                db_session.commit()

        return 'Analysis sent successfully', 200

    except Exception as e:
        print(f'Error found: {str(e)}')
        return f'Error found: {str(e)}', 500

