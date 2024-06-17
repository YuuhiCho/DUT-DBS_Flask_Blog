class BaseConfig(object):
    SECRET_KEY = 'secret key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1:3306/flask_blog?charset=utf8mb4'


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://zyh:flaskblog@127.0.0.1:3306/flask_blog?charset=utf8mb4'
