from config import Chart
from flask import Flask, jsonify
from flask import request
from config import Session as DBSession 
from flask import Blueprint

save_new_chart = Blueprint('saveChart', __name__)

@save_new_chart.route('/save_chart', methods=['POST'])
def save_chart():
    try:
        # Obtener datos del cuerpo de la solicitud (POST request)
        data = request.json

        # Crear una nueva instancia de la clase Chart con los datos proporcionados
        new_chart = Chart(
            support_1=data.get('support_1'),
            support_2=data.get('support_2'),
            support_3=data.get('support_3'),
            support_4=data.get('support_4'),
            resistance_1=data.get('resistance_1'),
            resistance_2=data.get('resistance_2'),
            resistance_3=data.get('resistance_3'),
            resistance_4=data.get('resistance_4'),
            coin_bot_id=data.get('coin_bot_id')
            # Puedes agregar más campos según sea necesario
        )

        # Eliminar todas las filas donde coin_bot_id sea igual al proporcionado
        with DBSession() as db_session:
            delete_last_chart = db_session.query(Chart).filter_by(coin_bot_id=data.get('coin_bot_id')).delete()
            print(f"{delete_last_chart} rows deleted")

            # Guardar el nuevo objeto Chart en la base de datos
            db_session.add(new_chart)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Chart saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})