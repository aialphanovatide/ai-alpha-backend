from flask import Blueprint, jsonify, request

webhook_bp = Blueprint('webhook_bp', __name__)

@webhook_bp.route('/tradingview-webhook', methods=['POST'])
def tradingview_webhook():
    # Verificar si los datos se reciben correctamente
    data = request.json
    print(f"Alerta recibida: {data}")
    
    # Puedes procesar los datos aquí, por ejemplo, enviarlos a otro servicio o guardarlos
    return jsonify({"status": "success", "message": "Alerta recibida correctamente"}), 200