"""
Flask веб-приложение для управления долгами
Роль: Разработчик - создание веб-приложения
"""
from flask import Flask, render_template
from src.web.api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

