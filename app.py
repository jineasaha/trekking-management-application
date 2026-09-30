from flask import Flask
from config import Config
from extensions import db, login_manager

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager.init_app(app)

login_manager.login_view = "main.login"

from routes import main

app.register_blueprint(main)

if __name__ == "__main__":
    app.run(debug=True)