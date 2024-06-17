from exts import db
import datetime
import shortuuid


# 所有的ORM模型都继承自db.Model类，与数据库进行交互
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(100), primary_key=True, default=shortuuid.uuid)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(100), nullable=False)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'))
    user = db.relationship('User',
                           backref=db.backref('posts',
                                              lazy='dynamic',
                                              order_by=created_time.desc()
                                              )
                           )
    # 文章对应的tag的id外键
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'))
    # 名为tag的关系，将Post关联到Tag模型，可以通过Post对象来访问对应Tag的属性
    tag = db.relationship('Tag',
                          backref=db.backref('posts',
                                             lazy='dynamic',
                                             order_by=created_time.desc()
                                             )
                          )


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    local_time = db.Column(db.DateTime)
    like_count = db.Column(db.Integer, default=0)
    commenter_name = db.Column(db.Text, nullable=False)
    commenter_email = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    post = db.relationship('Post',
                           backref=db.backref('comments',
                                              lazy='dynamic',
                                              order_by=created_time.desc()
                                              )
                           )
