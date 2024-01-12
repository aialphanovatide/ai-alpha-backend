import os

import bcrypt
<<<<<<< HEAD
from config import Admin, Category, Chart, CoinBot, Keyword
#from routes.slack.templates.product_alert_notification import send_notification_to_product_alerts_slack_channel
=======
from config import Admin, Category
>>>>>>> de7da41ee4ba334a688155ae3963566f9633f369
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.trendspider.index import trendspider_notification_bp
from routes.tradingview.index import tradingview_notification_bp
from routes.news_bot.index import activate_news_bot, deactivate_news_bot, scrapper_bp
from routes.telegram.index import telegram_bp 
from routes.slack.slack_actions import slack_events_bp
from flask_cors import CORS
from websocket.socket import socketio
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import Unauthorized



app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)

# Register blueprints
app.register_blueprint(telegram_bp)
app.register_blueprint(scrapper_bp)
app.register_blueprint(send_email_bp)
app.register_blueprint(slack_events_bp)
app.register_blueprint(trendspider_notification_bp)
app.register_blueprint(tradingview_notification_bp)

@app.route('/home')
def dashboard():
    if 'user_id' not in flask_session:
        return redirect(url_for('login'))

    # Obtener datos de la tabla category
    with DBSession() as db_session:
        categories = db_session.query(Category).all()   
    
    ## Antes de renderizar la plantilla, verifica si hay algún bot inactivo
    any_inactive = any(not category.is_active for category in categories)
    return render_template('home/index.html', categories=categories, any_inactive=any_inactive)

@app.route('/activate_bot', methods=['POST'])
def activate_bot():
    try:
        with DBSession() as db_session:
            categories = db_session.query(Category).all()

        for category in categories:
            print(category.category)
            activate_news_bot(category.category)
        any_inactive = any(not category.is_active for category in categories)
        return jsonify({"bots": [{"category": category.category, "isActive": category.is_active} for category in categories], "any_inactive": any_inactive})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deactivate_bot', methods=['POST'])
def deactivate_bot():
    try:
        with DBSession() as db_session:
            categories = db_session.query(Category).all()

        for category in categories:
            deactivate_news_bot(category.category)

        any_inactive = any(not category.is_active for category in categories)
        return jsonify({"bots": [{"category": category.category, "isActive": category.is_active} for category in categories], "any_inactive": any_inactive})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        # Obtener datos del formulario
        data = request.json  # Utiliza request.json para obtener datos JSON directamente
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        print('pass: ', password)
        print('user: ', username)
        print('email: ', email)

        # Verificar que la contraseña no sea None
        if password is None:
            return jsonify({'success': False, 'message': 'Invalid password'})

        # Crear un nuevo objeto Admin y guardar en la base de datos
        new_admin = Admin(username=username, mail=email, password=password)

        # Utiliza la sesión de SQLAlchemy que has definido en config.py
        with DBSession() as db_session:
            db_session.add(new_admin)
            db_session.commit()

        # Puedes devolver un JSON indicando el éxito del registro
        return jsonify({'success': True, 'message': 'Registration successful'})

    # Si la solicitud no es POST, devolver un mensaje de error
    return jsonify({'success': False, 'message': 'Invalid request'})

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')


        # Verifica las credenciales en la base de datos
        with DBSession() as db_session:
            try:
                user = db_session.query(Admin).filter_by(username=username).one()
                # Comparar contraseñas directamente
                if user.password == password:
                    # Autenticación exitosa, puedes devolver datos del usuario y otras cosas que puedas necesitar en el cliente
                    return jsonify({'success': True, 'user': {'admin_id': user.admin_id, 'username': user.username, 'email': user.mail}})
                else:
                    # Contraseña incorrecta
                    return jsonify({'success': False, 'message': 'Invalid password'})
            except NoResultFound:
                # Usuario no encontrado
                return jsonify({'success': False, 'message': 'Invalid username'})
    
    

    # Si la solicitud no es POST, devolver un mensaje de error
    return jsonify({'success': False, 'message': 'Invalid request'})


@app.route('/bots')
def bots():
    if 'user' not in flask_session:
        return redirect(url_for('login'))

    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    for category in categories:
        print(category.category)
        activate_news_bot(category.category)

    any_inactive = any(not category.is_active for category in categories)

    return render_template('home/bots.html', admin=flask_session['user'], categories=categories, any_inactive=any_inactive)


@app.route('/get_all_bots', methods=['GET'])
def get_all_bots():

    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    # Transformar la información de las categorías a un formato deseado
    bots = [{'category': category.category, 'isActive': category.is_active} for category in categories]
    

    return jsonify({'success': True, 'bots': bots})

@app.route('/get_bot_status')
def get_bot_status():
    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    bot_statuses = {category.category: category.is_active for category in categories}
    print(bot_statuses)
    return jsonify({'success': True, 'bot_statuses': bot_statuses})

@app.route('/save_chart', methods=['POST'])
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

        # Guardar el nuevo objeto Chart en la base de datos
        with DBSession() as db_session:
            db_session.add(new_chart)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Chart saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    

@app.route('/save_keyword', methods=['POST'])
def save_keyword():
    try:
        # Obtener datos del cuerpo de la solicitud (POST request)
        data = request.json

        # Crear una nueva instancia de la clase Keyword con los datos proporcionados
        new_keyword = Keyword(
            word=data.get('keyword'),  # Cambiado de 'keyword' a 'word'
            coin_bot_id=data.get('coin_bot_id')
            # Puedes agregar más campos según sea necesario
        )

        # Guardar el nuevo objeto Keyword en la base de datos
        with DBSession() as db_session:
            db_session.add(new_keyword)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Keyword saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/get_all_coin_bots', methods=['GET'])
def get_all_coin_bots():
    try:
        with DBSession() as db_session:
            coin_bots = db_session.query(CoinBot.bot_id, CoinBot.bot_name).all()

        # Transformar la lista de tuplas a una lista de diccionarios
        coin_bots_data = [{'id': bot_id, 'name': bot_name} for bot_id, bot_name in coin_bots]

        return jsonify({'success': True, 'coin_bots': coin_bots_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/get_keywords_for_coin_bot/<int:coin_bot_id>', methods=['GET'])
def get_keywords_for_coin_bot(coin_bot_id):
    print(coin_bot_id)
    try:
        with DBSession() as db_session:
            # Obtener las palabras clave para el coinBot específico
            keywords = db_session.query(Keyword).filter_by(coin_bot_id=coin_bot_id).all()
            keywords_data = [{'id': keyword.keyword_id, 'word': keyword.word} for keyword in keywords]
            return jsonify({'success': True, 'keywords': keywords_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    
@app.route('/delete_keyword', methods=['POST'])
def delete_keyword():
    try:
        keyword_id = request.json.get('keyword_id')
        print('keyword_id', keyword_id)
        with DBSession() as db_session:
            keyword = db_session.query(Keyword).filter_by(keyword_id=keyword_id).first()
            print('keyword :', keyword)

            if keyword:
                db_session.delete(keyword)
                db_session.commit()
                return jsonify({'success': True, 'message': 'Keyword deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Keyword not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/logout', methods=['GET'])
def logout():
    # Verificar si el usuario está autenticado
    if 'user_id' in flask_session:
        # Limpiar la sesión del usuario para cerrar la sesión
        flask_session.pop('user_id', None)
        return jsonify({'success': True, 'message': 'Logout successful'})
    else:
        # Si el usuario no está autenticado, lanzar una excepción Unauthorized
        raise Unauthorized()


if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') 
        socketio.run(app, port=9000, debug=False, use_reloader=False) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")
    finally:
        print('---AI Alpha server was stopped---')

