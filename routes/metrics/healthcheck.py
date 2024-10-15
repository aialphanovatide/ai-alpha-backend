# routes/metrics/healthcheck.py

from flask import Blueprint, jsonify

healthcheck = Blueprint('healthcheck', __name__)

@healthcheck.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200
