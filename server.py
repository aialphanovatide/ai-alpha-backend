import os
from config import Admin, Category
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
        return render_template('home/index.html', categories=categories, any_inactive=any_inactive)

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
        return render_template('home/index.html', categories=categories, any_inactive=any_inactive)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Obtener datos del formulario  
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Crear un nuevo objeto Admin y guardar en la base de datos
        new_admin = Admin(username=username, mail=email, password=password)

        # Utiliza la sesión de SQLAlchemy que has definido en config.py
        with DBSession() as db_session:  # Cambia el nombre aquí también
            db_session.add(new_admin)
            db_session.commit()

        # Redirigir a la página de inicio de sesión u otra página después del registro
        return redirect(url_for('login'))

    return render_template('home/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("try login")
        username = request.form.get('username')
        password = request.form.get('password')

        # Verifica las credenciales en la base de datos
        with DBSession() as db_session:
            user = db_session.query(Admin).filter_by(username=username, password=password).first()
            categories = db_session.query(Category).all()
        if user:
            # Autenticación exitosa, inicia sesión
            flask_session['user_id'] = user.admin_id
            flask_session['user'] = {'admin_id': user.admin_id, 'username': user.username, 'email': user.mail}
            
            any_inactive = any(not category.is_active for category in categories)

            return render_template('home/index.html', admin=flask_session['user'], categories=categories, any_inactive=any_inactive)
        else:
            # Credenciales incorrectas
            print("Account access denied")
            return render_template('home/login.html', error='Invalid username or password')

    # Si la solicitud es GET, simplemente renderiza el formulario de inicio de sesión
    return render_template('home/login.html')

@app.route('/bots')
def bots():
    # Verificar si el usuario ha iniciado sesión
    if 'user' not in flask_session:
        return redirect(url_for('login'))

    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    for category in categories:
        print(category.category)
        activate_news_bot(category.category)

    any_inactive = any(not category.is_active for category in categories)

    return render_template('home/bots.html', admin=flask_session['user'], categories=categories, any_inactive=any_inactive)

@app.route('/logout', methods=['POST'])
def logout():   
    # Clear the user session to log them out
    flask_session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') 
        socketio.run(app, port=9000, debug=False, use_reloader=False) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")
    finally:
        print('---AI Alpha server was stopped---')

