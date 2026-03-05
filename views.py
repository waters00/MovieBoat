import datetime
import re

from flask import render_template, request, redirect, url_for, jsonify, abort
from flask_login import current_user, login_user, logout_user, LoginManager, login_required

from models import db
from models import Movie, User, ConsumeRecord, ChargeRecord, Comment
from utils import Pagination
from app import app

PHONE_RE = re.compile(r"^1[3-9][0-9]{9}$")


def _clean(value):
    return (value or "").strip()


def _utcnow_naive():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


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
    logout_user()
    return redirect(url_for('.index'))


@app.route('/login', methods=['POST'])
def login():
    phone = _clean(request.form.get('phone'))
    password = _clean(request.form.get('password'))

    if not phone or not password:
        return jsonify({'code': 103, 'message': '请输入手机号和密码'})

    if not PHONE_RE.match(phone):
        return jsonify({'code': 104, 'message': '手机号格式不正确'})

    user = User.query.filter_by(phone_number=phone).first()

    if not user:
        return jsonify({'code': 101, 'message': '用户不存在'})

    if user.validate_password(password):
        login_user(user)
        return jsonify({'code': 100, 'message': '登录成功'})

    return jsonify({'code': 102, 'message': '密码错误'})


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    movie = Movie.query.filter_by(brief_id=movie_id).first()
    if not movie:
        abort(404)

    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('.movie_detail', movie_id=movie_id))

        comment = _clean(request.form.get('comment'))
        if comment:
            u = db.session.get(User, current_user.get_id())
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
    if not current_user.is_authenticated:
        return jsonify({'code': 301, 'message': '请先登录'})

    movie_brief_id = _clean(request.form.get('movie_brief_id'))
    if not movie_brief_id:
        return jsonify({'code': 303, 'message': '请求参数错误'})

    movie_brief_id = movie_brief_id.split('_')[-1]
    if not movie_brief_id.isdigit():
        return jsonify({'code': 303, 'message': '请求参数错误'})

    movie = Movie.query.filter_by(brief_id=int(movie_brief_id)).first()
    if not movie:
        return jsonify({'code': 304, 'message': '影片不存在'})

    movie_price = movie.movie_price.first()
    if not movie_price:
        return jsonify({'code': 305, 'message': '影片价格未配置'})

    u = db.session.get(User, current_user.get_id())
    if not u:
        return jsonify({'code': 301, 'message': '请先登录'})

    consumed = ConsumeRecord.query.filter_by(consumer_id=u.id, movie_id=movie.id).first()
    if consumed:
        return jsonify({'code': 306, 'message': '已购买该影片，无需重复购买'})

    money = float(movie_price.price)
    if u.balance < money:
        return jsonify({'code': 302, 'message': '余额不足，请先充值!'})

    u.balance -= money
    cr = ConsumeRecord(
        consumer=u,
        movie=movie,
        consume_time=_utcnow_naive(),
        money=money,
    )

    db.session.add(u)
    db.session.add(cr)
    db.session.commit()
    return jsonify({'code': 300, 'message': '购买成功!'})


@app.route('/user/message', methods=['GET'])
@login_required
def message():
    u = db.session.get(User, current_user.get_id())
    messages = []
    print(u.u_comments.all())

    for comment in u.u_comments.all():
        for reply in comment.replies.all():
            messages.append(reply)

    return render_template('message.html', user=current_user, messages=messages)


@app.route('/user/charge', methods=['GET', 'POST'])
@login_required
def charge():
    if request.method == 'POST':
        charge_amount = _clean(request.form.get('charge_amount'))
        if not charge_amount.isdigit() or int(charge_amount) <= 0:
            return render_template('charge.html', user=current_user)

        charge_amount = int(charge_amount)
        u = db.session.get(User, current_user.get_id())
        u.balance += charge_amount

        cr = ChargeRecord(
            user=u,
            charge_time=_utcnow_naive(),
            money=charge_amount
        )
        db.session.add(cr)
        db.session.add(u)
        db.session.commit()

    return render_template('charge.html', user=current_user)


@app.route('/register', methods=['POST'])
def register():
    username = _clean(request.form.get('username'))
    password = _clean(request.form.get('password'))
    phone = _clean(request.form.get('phone'))

    if not username:
        return jsonify({'code': 203, 'message': '用户名不能为空'})

    if not PHONE_RE.match(phone):
        return jsonify({'code': 203, 'message': '手机号格式不正确'})

    if len(password) < 6:
        return jsonify({'code': 204, 'message': '密码长度至少为6位'})

    user = User.query.filter_by(phone_number=phone).first()
    if user:
        return jsonify({'code': 201, 'message': '此手机已经被注册'})

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'code': 202, 'message': '此用户名已经被注册'})

    user = User(
        username=username,
        phone_number=phone,
        password=password
    )
    db.session.add(user)
    db.session.commit()

    login_user(user)

    return jsonify({'code': 200, 'message': '注册成功'})


@app.route('/user/consume_history', methods=['GET'])
@login_required
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


@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_phone_number = request.form.get('phone_number')
        print(new_username, new_phone_number)

        u = db.session.get(User, current_user.get_id())
        u.username = new_username
        u.phone_number = new_phone_number
        db.session.add(u)
        db.session.commit()

    return render_template('profile.html', user=current_user)


@app.route('/user/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('password')
        password_repeated = request.form.get('password_repeated')

        if new_password == password_repeated:
            u = db.session.get(User, current_user.get_id())
            print(u.password)
            u.password = new_password
            print(u.password)

            db.session.add(u)
            db.session.commit()

    return render_template('change_password.html', user=current_user)
