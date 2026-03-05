import datetime

from flask import render_template, request, redirect, url_for, session, jsonify, abort
from flask_login import current_user, login_user, logout_user, LoginManager, login_required

from models import db
from models import Movie, User, ConsumeRecord, ChargeRecord, Comment
from utils import Pagination
from app import app


def init_login():
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)


@app.route('/', methods=['GET'])
@app.route('/search', methods=['GET'])
def index():
    keyword = request.args.get('keyword', None)
    page = int(request.args.get('page', 1))

    PER_PAGE = 8

    if not keyword:
        movies = Movie.query.all()
    else:
        movies = Movie.query.filter(Movie.title.like('%' + keyword + '%')).all()

    pagination = Pagination(page, PER_PAGE, len(movies))

    tmp = (page - 1) * PER_PAGE
    movies = movies[tmp:tmp + PER_PAGE]

    if current_user.is_authenticated:
        for movie in movies:
            movie.can_watche = False

        consume_records = ConsumeRecord.query.filter_by(consumer=current_user).all()
        bought_moveis = [record.movie for record in consume_records]
        print(bought_moveis)

        for movie in movies:
            if movie in bought_moveis:
                movie.can_watched = True

    current_path = request.url.split('page')[0]

    if current_path.endswith('/'):
        current_path += '?'

    return render_template(
        'index.html',
        user=current_user,
        movies=movies,
        keyword=keyword,
        current_path=current_path,
        current_page=page,
        pagination=pagination
    )


@app.route('/logout')
@login_required
def logout():
    user = User.query.get(session.get('user_id'))
    logout_user()
    return redirect(url_for('.index'))


@app.route('/login', methods=['POST'])
def login():
    print(request.form)
    phone = request.form.get('phone')
    password = request.form.get('password')

    user = User.query.filter_by(phone_number=phone).first()

    ret = {}

    if not user:
        ret['code'] = 101
        ret['message'] = '用户不存在'
        return jsonify(ret)

    if user.validate_password(password):
        ret['code'] = 100
        login_user(user)
    else:
        ret['code'] = 102
        ret['message'] = '密码错误'

    return jsonify(ret)


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    movie = Movie.query.filter_by(brief_id=movie_id).first()
    if request.method == 'POST':
        print(request.form.get('comment'))
        comment = request.form.get('comment')
        u = User.query.filter_by(id=current_user.get_id()).first()

        c = Comment(
            user=u,
            movie=movie,
            comment_time=datetime.datetime.now(),
            content=comment,
            point=5,
        )
        db.session.add(c)
        db.session.commit()

    comments = movie.comments.all()

    can_watched = False
    if current_user.is_authenticated:
        consume_records = ConsumeRecord.query.filter_by(consumer=current_user).all()
        bought_moveis = [record.movie for record in consume_records]
        if movie in bought_moveis:
            can_watched = True

    if not movie:
        abort(404)

    return render_template(
        'movie_detail.html',
        movie=movie,
        user=current_user,
        comments=comments,
        can_watched=can_watched,
    )


@app.route('/watch/<movie_id>', methods=['GET'])
def watch(movie_id):
    movie = Movie.query.filter_by(brief_id=movie_id).first()
    if not movie:
        abort(404)
    return render_template('watch.html', movie=movie, user=current_user)


@app.route('/consume', methods=['POST'])
def consume():
    print(request.form)
    movie_brief_id = request.form.get('movie_brief_id')
    movie_brief_id = movie_brief_id.split('_')[-1]
    movie = Movie.query.filter_by(brief_id=movie_brief_id).first()
    print(movie)

    ret = {}

    if not current_user.is_active:
        ret['code'] = 301
        ret['message'] = '请先登录'
        return jsonify(ret)

    money = movie.movie_price.first().price

    u = User.query.filter_by(id=current_user.get_id()).first()

    if u.balance >= money:
        u.balance -= money

        cr = ConsumeRecord(
            consumer=current_user,
            movie=movie,
            consume_time=datetime.datetime.utcnow(),
            money=money,
        )

        db.session.add(u)
        db.session.add(cr)
        db.session.commit()
        ret['code'] = 300
        ret['message'] = '购买成功!'

    else:
        ret['code'] = 302
        ret['message'] = '余额不足，请先充值!'

    return jsonify(ret)


@login_required
@app.route('/user/message', methods=['GET'])
def message():
    u = User.query.get(current_user.get_id())
    messages = []
    print(u.u_comments.all())

    for comment in u.u_comments.all():
        for reply in comment.replies.all():
            messages.append(reply)

    return render_template('message.html', user=current_user, messages=messages)


@app.route('/user/charge', methods=['GET', 'POST'])
def charge():
    if request.method == 'POST':
        charge_amount = int(request.form.get('charge_amount'))
        u = User.query.get(current_user.get_id())
        u.balance += charge_amount

        cr = ChargeRecord(
            user=u,
            charge_time=datetime.datetime.utcnow(),
            money=charge_amount
        )
        db.session.add(cr)
        db.session.add(u)
        db.session.commit()

    return render_template('charge.html', user=current_user)


@app.route('/register', methods=['POST'])
def register():
    print(request.form)
    username = request.form.get('username')
    password = request.form.get('password')
    phone = request.form.get('phone')
    print(username, password, phone)
    ret = {}

    user = User.query.filter_by(phone_number=phone).first()
    if user:
        ret['code'] = 201
        ret['message'] = '此手机已经被注册'
        return jsonify(ret)

    user = User.query.filter_by(username=username).first()
    if user:
        ret['code'] = 202
        ret['message'] = '此用户名已经被注册'
        return jsonify(ret)

    user = User(
        username=username,
        phone_number=phone,
        password=password
    )
    db.session.add(user)
    db.session.commit()

    login_user(user)

    ret['code'] = 200
    ret['message'] = '注册成功'

    return jsonify(ret)


@login_required
@app.route('/user/consume_history', methods=['GET'])
def custom_records():
    page = int(request.args.get('page', 1))
    PER_PAGE = 3

    consume_records = ConsumeRecord.query.filter_by(consumer=current_user).all()

    pagination = Pagination(page, PER_PAGE, len(consume_records))

    tmp = (page - 1) * PER_PAGE
    consume_records = consume_records[tmp:tmp + PER_PAGE]
    current_path = request.url.split('page')[0] + '?'

    return render_template(
        'consume_history.html',
        user=current_user,
        consume_records=consume_records,
        pagination=pagination,
        current_page=page,
        current_path=current_path,
    )


@login_required
@app.route('/user/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_phone_number = request.form.get('phone_number')
        print(new_username, new_phone_number)

        u = User.query.get(current_user.get_id())
        u.username = new_username
        u.phone_number = new_phone_number
        db.session.add(u)
        db.session.commit()

    return render_template('profile.html', user=current_user)


@login_required
@app.route('/user/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('password')
        password_repeated = request.form.get('password_repeated')

        if new_password == password_repeated:
            u = User.query.get(current_user.get_id())
            print(u.password)
            u.password = new_password
            print(u.password)

            db.session.add(u)
            db.session.commit()

    return render_template('change_password.html', user=current_user)
