from flask import Flask, jsonify, request, Blueprint
from config import Session as DBSession, Site


save_site_bp = Blueprint('save_site', __name__)

@save_site_bp.route('/save_site', methods=['POST'])
def save_site():
    try:
        # Obtener datos del cuerpo de la solicitud (POST request)
        data = request.json

        # Crear una nueva instancia de la clase Site con los datos proporcionados
        new_site = Site(
            coin_bot_id=data.get('coin_bot_id'),
            site_name=data.get('site_name'),
            base_url=data.get('base_url'),
            data_source_url=data.get('data_source_url'),
            is_URL_complete=data.get('is_URL_complete'),
            main_container=data.get('main_container')
        )

        # Guardar el nuevo objeto Site en la base de datos
        with DBSession() as db_session:
            db_session.add(new_site)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Site saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
