一个博客小项目，数据库课程大作业，用到数据库的地方其实只有一点点   
使用Flask + MySQL + Jinja2，可以直接代码部署   
时间紧，主打一个能动就行，书帮了很大忙   

### 实现功能：   
- 登录用户可撰写新文章
- 登录用户可删除已有文章
- 关键字检索（标签、正文、标题）
- 按照标签分类展示文章
- 删除文章不会造成标签冗余
- 任意游客可评论文章
- 登录用户可删除文章评论
- 提供链接可跳转的统计数据页面
- 可以点赞文章和评论并实时更新
- 可以显示文章阅读量
- 登录用户可以使用sql原语查询
- 游客无法进行登录用户专属操作

### 部署教程（Linux为例）：
1. 安装Git、MySQL、python3
2. 拉取代码
3. 设置数据库用户和权限，根据自己的数据库设置修改config.py
4. 在项目根目录下创建venv（也可以不创），执行`pip install -r requirements.txt`安装依赖
5. 执行`flask db upgrade`，迁移ORM模型至数据库
6. 执行`flask sys-init`，初始化系统并创建新用户。可以用`flask add-user`创建其他用户
7. 执行`pip install gunicorn`安装Gunicorn
8. 在项目根目录创建gunicorn.conf.py文件，文件中填入如下内容：
```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count()*2 + 1
daemon = True
```
10. 执行`gunicorn app:app`，启动服务，成功启动就可以使用IP+端口号访问项目网站
11. 如果访问不到，把上一步中的daemon修改为False，再使用gunicorn运行，看终端报错寻找解决办法
12. （可选）对项目网站进行反向代理，使用域名访问
---
参考资料：   
https://github.com/saucer-man/flask_blog   
黄勇 《Flask Web全栈开发实战》  清华大学出版社, 2022. 
