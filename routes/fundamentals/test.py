from config import session, Token_utility
from flask import Blueprint, request
from sqlalchemy import column, String


dynamic_bp = Blueprint('dynamic_bp', __name__)

@dynamic_bp.route('/competitor/add/column', methods=['POST'])
def add_column():

    data = request.data
    column_name = data['column_name']
    column_name = data['column_value']

    if column_name:
        column_name = column(String)
        Token_utility.add_column(column_name)

