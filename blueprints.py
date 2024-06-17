from datetime import timedelta
import flask
import pytz
from flask import Blueprint, jsonify, request, make_response
from tabulate import tabulate
from sqlalchemy.exc import SQLAlchemyError
from exts import db
from models import Post, Tag, User, Comment
from sqlalchemy import or_, text
from werkzeug.security import check_password_hash

# 创建蓝图对象
bp = Blueprint('blog', __name__)


# 主页
@bp.route('/')
@bp.route('/index/')
def index():
    page = flask.request.args.get('page', 1, type=int)
    # 实现分页，每页5篇文章
    pagination = Post.query.order_by(Post.created_time.desc()).paginate(
        page=page, per_page=5, error_out=False
    )
    posts = pagination.items
    # 实时计算评论数
    for post in posts:
        post.comment_count = post.comments.count()
        db.session.add(post)
        db.session.commit()
    return flask.render_template('index.html',
                                 posts=posts,
                                 pagination=pagination,
                                 no_posts_message="还没有任何文章！点击右上角登录后发布。")


# 关于页
@bp.route('/about/')
def about():
    return flask.render_template('about.html')


# 登录页，需要输入用户名密码所以需要添加POST方法
@bp.route('/login/', methods=['GET', 'POST'])
def login():
    # 已登录则不再重复登录
    if flask.session.get("user_id"):
        return flask.redirect(flask.url_for('blog.index'))
    # 初次进入登录页面，直接展示login.html，不对空白的输入框做验证
    if flask.request.method == 'GET':
        return flask.render_template('login.html')
    # 点击登录按钮后
    name = flask.request.form.get('name')
    user = User.query.filter(User.username == name).first()
    # 验证用户名
    if not user:
        flask.flash('不存在该用户，请重新输入！')
        return flask.render_template('login.html')
    # 验证密码
    is_pw_right = check_password_hash(user.password,
                                      flask.request.form.get('password'))
    if not is_pw_right:
        flask.flash('用户名或密码错误，请重新输入！')
        return flask.render_template('login.html')
    # 登录成功，添加会话
    flask.session['user_id'] = user.id
    return flask.redirect(flask.url_for('blog.index'))


# 注销
@bp.route('/logout/')
def logout():
    flask.session.clear()  # 清除所有的会话，包括user_id
    return flask.redirect(flask.url_for('blog.index'))


# 文章页
@bp.route('/post/<int:post_id>/')
def post(post_id):
    post_to_show = Post.query.get_or_404(post_id)
    user_timezone = 'Asia/Shanghai'  # 东8区
    # 将数据库中存储的UTC时间转换为北京时间
    local_tz = pytz.timezone(user_timezone)
    local_time = post_to_show.created_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
    # 查询文章对应的评论
    comments = post_to_show.comments
    # 将所有评论的创建时间转换为北京时间
    for comment in comments:
        comment.local_time = comment.created_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
        db.session.add(comment)
        db.session.commit()
    # 渲染出预计需要返回的页面
    response = make_response(
        flask.render_template('post.html',
                              post=post_to_show,
                              display_time=local_time,
                              comments=comments)
    )
    # 获取当前页面的cookie名称
    cookie_name = f'post_{post_id}_viewed'
    # 如果没有找到该cookie，识别为初次访问
    if not request.cookies.get(cookie_name):
        post_to_show.view_count += 1  # 阅读量+1
        db.session.add(post_to_show)
        db.session.commit()
        # 设置cookie，标记该浏览器已经访问过该页面，访问量不再增加
        response.set_cookie(cookie_name, 'true', max_age=timedelta(days=30))
    # 返回页面
    return response


# 文章点赞
@bp.route('/post/<int:post_id>/like/', methods=['POST'])
def like_post(post_id):
    post_to_like = Post.query.get_or_404(post_id)
    post_to_like.like_count += 1
    db.session.add(post_to_like)
    db.session.commit()
    return jsonify({'like_count': post_to_like.like_count, 'success': True})


# 评论文章
@bp.route('/post/<int:post_id>/comment/', methods=['POST'])
def create_comment(post_id):
    # 从文本框获取信息
    content = flask.request.form['content']
    commenter_name = flask.request.form['commenter_name']
    commenter_email = flask.request.form['commenter_email']
    # 创建并保存评论
    comment = Comment(content=content,
                      post_id=post_id,
                      commenter_name=commenter_name,
                      commenter_email=commenter_email)
    db.session.add(comment)
    db.session.commit()
    # 重定向至对应文章，加上#comment的页面锚点
    return flask.redirect(flask.url_for('blog.post',
                                        post_id=post_id) +
                          '#comment')


# 评论点赞
@bp.route('/comment/<int:comment_id>/like/', methods=['POST'])
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.like_count += 1
    db.session.add(comment)
    db.session.commit()
    return jsonify({'like_count': comment.like_count, 'success': True})


# 评论删除
@bp.route('/comment/<int:comment_id>/delete')
def delete_comment(comment_id):
    user_id = flask.session.get("user_id")
    if not user_id:  # 未登录则不允许删除
        flask.flash('请先登录再删除评论！')
        return flask.redirect(flask.url_for('blog.login'))
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    # 删除对应评论
    db.session.delete(comment)
    db.session.commit()
    # 重定向至对应文章，加上#comment的页面锚点
    return flask.redirect(flask.url_for('blog.post',
                                        post_id=post_id) +
                          '#comment')


# 发布文章
@bp.route('/publish/', methods=['GET', 'POST'])
def publish():
    # 未登录不允许进入发布页
    if not flask.session.get("user_id"):
        flask.flash('请先登录后再发布！')
        return flask.redirect(flask.url_for('blog.login'))
    user_id = flask.session.get("user_id")
    # 初次使用GET方法访问，直接返回发布页面
    if flask.request.method == 'GET':
        return flask.render_template('publish.html')
    # 按下发布按钮，方法变为POST
    # 获取文本框中的信息
    title = flask.request.form.get('title')
    content = flask.request.form.get('content')
    tagname = flask.request.form.get('tagname')

    if not tagname:  # 没输入标签
        tagname = '默认标签'

    # 寻找是否已经存在同名tag
    exist_tag = Tag.query.filter(Tag.tag_name == tagname).first()
    if exist_tag:  # tag已存在，加入原有的tag
        tag_id = exist_tag.id
    else:  # tag不存在，创建新的tag
        new_tag = Tag(tag_name=tagname)
        db.session.add(new_tag)
        db.session.commit()
        # 获取新创建的tag的id，用于创建新文章
        tag_id = new_tag.id
    # 创建新文章
    new_post = Post(title=title, content=content, tag_id=tag_id, user_id=user_id)
    db.session.add(new_post)
    db.session.commit()
    # 发布完成后重定向至该文章页
    return flask.redirect(flask.url_for('blog.post', post_id=new_post.id))


# 搜索页
@bp.route('/search/')
def search():
    query = flask.request.args.get('q')  # 搜索的关键字
    # 在文章标题、内容以及标签中搜索包含关键字的内容，降序排列
    posts = Post.query.join(Post.tag).filter(
        or_(Post.title.contains(query),
            Post.content.contains(query),
            Tag.tag_name.contains(query))
    ).order_by(Post.created_time.desc())

    # 搜索到的文章只用一页展示，每页展示数和搜索到的文章数相同
    pagination = posts.order_by(Post.created_time.desc()).paginate(
        page=1, per_page=posts.count(), error_out=False
    )
    posts = pagination.items
    return flask.render_template('index.html',
                                 posts=posts,
                                 pagination=pagination,
                                 no_posts_message="没有搜索到任何文章")


# 删除文章
@bp.route('/delete/<int:post_id>/')
def delete(post_id):
    user_id = flask.session.get("user_id")
    # 未登录不允许删除
    if not user_id:
        flask.flash('请先登录后再删除！')
        return flask.redirect(flask.url_for('blog.login'))
    # 搜索要删除的文章和文章对应的tag
    post_to_delete = Post.query.get_or_404(post_id)
    tag_to_check = Tag.query.get_or_404(post_to_delete.tag_id)

    # 删除文章
    db.session.delete(post_to_delete)
    # 如果没有同样标签的其他文章，就把标签也删掉
    if not Post.query.filter(Post.tag_id == tag_to_check.id).all():
        db.session.delete(tag_to_check)
    # 确认所有的数据库删除会话
    db.session.commit()
    return flask.redirect(flask.url_for('blog.index'))


# 编辑文章
@bp.route('/edit/<int:post_id>/', methods=['GET', 'POST'])
def edit(post_id):
    user_id = flask.session.get("user_id")
    # 未登录则不允许编辑
    if not user_id:
        flask.flash('请先登录后再编辑！')
        return flask.redirect(flask.url_for('blog.login'))
    # 搜索要编辑的文章，和对应的标签
    post_to_edit = Post.query.get_or_404(post_id)
    current_tag = Tag.query.get_or_404(post_to_edit.tag_id)
    # 初次进入编辑界面，预填充信息
    if flask.request.method == 'GET':
        # 把上面的文章和标签传入编辑页面
        return flask.render_template('edit.html',
                                     post=post_to_edit,
                                     tag=current_tag)
    # 按下编辑按钮，使用POST方法了
    title = flask.request.form.get('title')
    content = flask.request.form.get('content')
    tagname = flask.request.form.get('tagname')  # 新输入的tag
    if not tagname:  # 编辑页的tag一栏为空
        tagname = '默认分组'
    # 查找同名tag
    exist_tag = Tag.query.filter(Tag.tag_name == tagname).first()
    # 如果找到了同名tag
    if exist_tag:
        edited_tag_id = exist_tag.id
    else:
        # 用输入的标签名字创建新标签对象
        new_tag = Tag(tag_name=tagname)
        db.session.add(new_tag)
        db.session.commit()
        edited_tag_id = new_tag.id

    # 更新文章信息
    post_to_edit.title = title
    post_to_edit.content = content
    post_to_edit.tag_id = edited_tag_id
    db.session.add(post_to_edit)
    db.session.commit()

    # 检查旧标签是否还有关联的文章
    if not Post.query.filter(Post.tag_id == current_tag.id).all():
        db.session.delete(current_tag)  # 删除没有关联文章的旧标签
        db.session.commit()
    # 修改完毕跳转回当前文章
    return flask.redirect(flask.url_for('blog.post', post_id=post_id))


# 查看某一标签的文章
@bp.route('/tag/<int:tag_id>/')
def tag(tag_id):
    posts = Post.query.filter(Post.tag_id == tag_id).order_by(Post.created_time.desc())
    # 所有相同标签文章只用一页展示
    pagination = posts.paginate(
        page=1, per_page=posts.count(), error_out=False
    )
    posts = pagination.items
    return flask.render_template('index.html',
                                 posts=posts,
                                 pagination=pagination,
                                 tag=tag_id,
                                 no_posts_message="不存在该标签")


# 查看统计数据
@bp.route('/statistics/')
def statistics():
    # 统计每个标签对应的文章数量
    tag_post_counts = db.session.execute(text(
        'SELECT tags.id, tags.tag_name, COUNT(posts.id) '
        'FROM tags '
        'JOIN posts ON posts.tag_id = tags.id '
        'GROUP BY tags.id, tags.tag_name '
        'ORDER BY COUNT(posts.id) DESC;'
        )
    )
    # 统计每篇文章对应的评论数量
    post_comment_counts = db.session.execute(text(
        'SELECT posts.id, posts.title, COUNT(comments.id) '
        'FROM posts '
        'JOIN comments ON posts.id = comments.post_id '
        'GROUP BY posts.id, posts.title '
        'ORDER BY COUNT(comments.id) DESC;'
        )
    )
    # 统计每篇文章的访问量
    post_view_counts = db.session.execute(text(
        'SELECT id, title, view_count '
        'FROM posts '
        'WHERE view_count > 0 '
        'ORDER BY view_count DESC;'
        )
    )
    # 统计每篇文章的点赞数
    post_like_counts = db.session.execute(text(
        'SELECT id, title, like_count '
        'FROM posts '
        'WHERE like_count > 0 '
        'ORDER BY like_count DESC;'
        )
    )
    # 统计每个评论者的的点赞数
    comment_like_counts = db.session.execute(text(
        'SELECT posts.id, commenter_name, comments.like_count, posts.title '
        'FROM comments, posts '
        'WHERE posts.id = comments.post_id AND comments.like_count > 0 '
        'ORDER BY like_count DESC;'
        )
    )
    return flask.render_template(
        'statistics.html',
        tag_post_counts=tag_post_counts,
        post_comment_counts=post_comment_counts,
        post_view_counts=post_view_counts,
        post_like_counts=post_like_counts,
        comment_like_counts=comment_like_counts
    )


@bp.route('/sql_search/', methods=['GET', 'POST'])
def sql_search():
    # 未登录则不允许查询
    if not flask.session.get("user_id"):
        flask.flash('请先登录后再查询！')
        return flask.redirect(flask.url_for('blog.login'))
    # 处理查询语句字符串，仅允许使用包含select的语句查询
    sql_query = flask.request.args.get('sql_query').lower()
    if 'select' not in sql_query:
        return flask.render_template(
            'sql_search.html',
            results='请输入合法的查询语句！'
        )
    try:  # 异常处理，如语法错误就获取错误信息
        result = db.session.execute(text(sql_query)).mappings().all()
        result = tabulate(result, headers='keys', tablefmt='psql')
    except SQLAlchemyError as e:
        db.session.rollback()
        result = str(e)
    return flask.render_template(
        'sql_search.html',
        results=result
    )


# 上下文处理器，渲染蓝图前调用
@bp.context_processor
def context_processor():
    user_id = flask.session.get("user_id")
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            # 让所有蓝图都能访问user->在html中能通过user判断是否登录
            return {'user': user}
    return {}
