from config import Analysis, AnalysisImage
from flask import Flask, jsonify
from config import Session as DBSession 
from flask import Blueprint


get_analysis_by_id = Blueprint('getAnalysisID', __name__)

@get_analysis_by_id.route('/get_analysis/<int:coin_bot_id>', methods=['GET'])
def get_analysis(coin_bot_id):
    with DBSession() as db_session:
        analysis_objects = db_session.query(Analysis).filter_by(coin_bot_id=coin_bot_id).all()

       
        analysis_data = []
        for analy in analysis_objects:
            analysis_dict = analy.to_dict() 

            images_objects = db_session.query(AnalysisImage).filter_by(analysis_id=analy.analysis_id).all()
            images_data = [{'image_id': img.image_id, 'image': img.image} for img in images_objects]

            analysis_dict['analysis_images'] = images_data
            analysis_data.append(analysis_dict)

        for analy in analysis_data:
            print(f"Analysis ID: {analy['analysis_id']}, Analysis: {analy['analysis']}, Created At: {analy['created_at']}")
            for img in analy['analysis_images']:
                print(f"  Image ID: {img['image_id']}, Image: {img['image']}")

        return jsonify(analysis_data)
