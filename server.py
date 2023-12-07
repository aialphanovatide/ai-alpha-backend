import os
from config import Admin
#from routes.slack.templates.product_alert_notification import send_notification_to_product_alerts_slack_channel
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.trendspider.index import trendspider_notification_bp
from routes.tradingview.index import tradingview_notification_bp
from routes.news_bot.index import scrapper_bp
from routes.telegram.index import telegram_bp 
from flask_cors import CORS
from flask import Flask, render_template, session as flask_session
from flask import request, redirect, url_for
from config import engine, Session as DBSession  # Cambia el nombre aquí también

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)

# Register blueprints
app.register_blueprint(telegram_bp)
app.register_blueprint(scrapper_bp)
app.register_blueprint(send_email_bp)
app.register_blueprint(trendspider_notification_bp)
app.register_blueprint(tradingview_notification_bp)


@app.route('/home')
def dashboard():
    # Comprueba si el usuario está autenticado
    if 'user_id' not in flask_session:
        return redirect(url_for('login'))
    return render_template('home/index.html')
    # Resto de la lógica para el dashboard

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

        if user:
            # Autenticación exitosa, inicia sesión
            flask_session['user_id'] = user.admin_id
            flask_session['user'] = {'admin_id': user.admin_id, 'username': user.username, 'email': user.mail}
            return render_template('home/index.html', admin=flask_session['user'])
        else:
            # Credenciales incorrectas
            return render_template('home/login.html', error='Invalid username or password')

    # Si la solicitud es GET, simplemente renderiza el formulario de inicio de sesión
    return render_template('home/login.html')

@app.route('/logout', methods=['POST'])
def logout():
    # Clear the user session to log them out
    flask_session.pop('user_id', None)
    return redirect(url_for('login'))

# Resto del código ...

if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---')
        app.run(threaded=True, debug=False, port=9000, use_reloader=True) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")

print('---AI Alpha server was stopped---')
