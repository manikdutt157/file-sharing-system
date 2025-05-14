from app import create_app
from app.utils.auth import jwt

app = create_app()
jwt.init_app(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)