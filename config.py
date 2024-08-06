class Config:
    SQLALCHEMY_DATABASE_URI = "mysql://slp:slp%2F6%2F03%2F20@localhost:3306/wi_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_API_KEY = "admin_api_key"
    SECRET_KET = "secret_key"
    JWT_SECRET_KEY = "jwt_secret_key"
