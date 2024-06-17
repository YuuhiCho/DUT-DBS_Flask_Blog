from flask import Flask
from werkzeug.security import generate_password_hash
from exts import db
from blueprints import bp
from flask_migrate import Migrate
from models import User
import config


app = Flask(__name__)
# 使用开发配置
app.config.from_object(config.DevelopmentConfig)
# 创建迁移对象
migrate = Migrate(app, db)
# 初始化db
db.init_app(app)
# 注册蓝图
app.register_blueprint(bp)


# 重置整个系统的命令
@app.cli.command("system-init")
def system_init():
    # 删除所有表后重建
    db.drop_all()
    db.create_all()
    # 输入用户
    user1 = User(username=input('请输入用户名：'))
    user1.password = generate_password_hash(input('请输入密码：'))
    db.session.add(user1)
    db.session.commit()


# 添加新用户的命令
@app.cli.command("add-user")
def add_user():
    # 输入用户
    user1 = User(username=input('请输入用户名：'))
    user1.password = generate_password_hash(input('请输入密码：'))
    db.session.add(user1)
    db.session.commit()
    print(f'成功添加新用户{user1.username}')


if __name__ == '__main__':
    app.run()
