from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')

if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') # Once the server is ready. Add a pin message to slack
        app.run(threaded=True, debug=False, port=7000, use_reloader=False) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")      

print('---AI Alpha server was stopped---')