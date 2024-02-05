from flask import Flask, jsonify, request
from config import Session as DBSession, Site
from flask import Blueprint
from flask_cors import cross_origin

erase_site = Blueprint('eraseSites', __name__)

@erase_site.route('/erase_site_by_id', methods=['POST'])
@cross_origin(supports_credentials=True)
def erase_site_by_id():
    try:
        site_id = request.json.get('site_id')
        print('site_id', site_id)
        
        with DBSession() as db_session:
            site = db_session.query(Site).filter_by(site_id=site_id).first()
            print('site:', site)

            if site:
                db_session.delete(site)
                db_session.commit()
                return jsonify({'success': True, 'message': 'Site deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Site not found'}), 404  # Indicar código de estado 404 para recurso no encontrado
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'success': False, 'error': str(e)}), 500  # Indicar código de estado 500 para error interno del servidor

def erase_site_by_id():
    try:
        site_id = request.json.get('site_id')
        print('site_id', site_id)
        
        with DBSession() as db_session:
            site = db_session.query(Site).filter_by(id=site_id).first()
            print('site:', site)

            if site:
                db_session.delete(site)
                db_session.commit()
                return jsonify({'success': True, 'message': 'Site deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Site not found'}), 404  # Indicar código de estado 404 para recurso no encontrado
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'success': False, 'error': str(e)}), 500  # Indicar código de estado 500 para error interno del servidor
