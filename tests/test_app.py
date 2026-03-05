import time

import pytest

from app import app, db
from models import ChargeRecord, ConsumeRecord, Movie, MoviePrice, User
from views import init_login


@pytest.fixture(scope="session", autouse=True)
def _setup_login_manager():
    init_login()


@pytest.fixture()
def client():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def _create_movie(brief_id=1001, price=12.0):
    movie = Movie(
        title=f"测试电影-{brief_id}",
        brief_id=brief_id,
        cover="https://example.com/not-found-cover.jpg",
        info="类型:剧情\n地区:中国\n年份:2024\n",
        summary="一部用于测试的电影。",
        video_uri="https://example.com/video.mp4",
    )
    movie_price = MoviePrice(movie=movie, price=price)
    db.session.add(movie)
    db.session.add(movie_price)
    db.session.commit()
    return movie


def _create_user(phone, username="test_user", balance=0.0):
    user = User(username=username, phone_number=phone, balance=balance)
    user.password = "pass123"
    db.session.add(user)
    db.session.commit()
    return user


def test_home_page_uses_modern_assets_and_image_fallback(client):
    with app.app_context():
        _create_movie()
    response = client.get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "bootstrap@5.3.8" in body
    assert "data-fallback=\"/static/img/movie_placeholder.svg\"" in body


def test_register_and_login(client):
    unique = str(int(time.time() * 1000))[-8:]
    phone = f"138{unique}"

    register_resp = client.post(
        "/register",
        data={"username": f"user_{unique}", "phone": phone, "password": "pass123"},
    )
    login_resp = client.post(
        "/login",
        data={"phone": phone, "password": "pass123"},
    )

    assert register_resp.status_code == 200
    assert register_resp.get_json()["code"] == 200
    assert login_resp.status_code == 200
    assert login_resp.get_json()["code"] == 100


def test_login_validation_and_wrong_password(client):
    with app.app_context():
        _create_user(phone="13800000009", username="login_user", balance=0.0)

    missing_resp = client.post("/login", data={"phone": "", "password": ""})
    assert missing_resp.status_code == 200
    assert missing_resp.get_json()["code"] == 103

    invalid_phone_resp = client.post("/login", data={"phone": "123456", "password": "pass123"})
    assert invalid_phone_resp.status_code == 200
    assert invalid_phone_resp.get_json()["code"] == 104

    wrong_password_resp = client.post("/login", data={"phone": "13800000009", "password": "wrong-pass"})
    assert wrong_password_resp.status_code == 200
    assert wrong_password_resp.get_json()["code"] == 102


def test_register_validation_and_duplicate(client):
    with app.app_context():
        _create_user(phone="13800000008", username="registered_name", balance=0.0)

    empty_name_resp = client.post(
        "/register",
        data={"username": "", "phone": "13800000010", "password": "pass123"},
    )
    assert empty_name_resp.status_code == 200
    assert empty_name_resp.get_json()["code"] == 203

    invalid_phone_resp = client.post(
        "/register",
        data={"username": "foo", "phone": "110", "password": "pass123"},
    )
    assert invalid_phone_resp.status_code == 200
    assert invalid_phone_resp.get_json()["code"] == 203

    short_password_resp = client.post(
        "/register",
        data={"username": "foo", "phone": "13800000010", "password": "12345"},
    )
    assert short_password_resp.status_code == 200
    assert short_password_resp.get_json()["code"] == 204

    duplicate_phone_resp = client.post(
        "/register",
        data={"username": "new_name", "phone": "13800000008", "password": "pass123"},
    )
    assert duplicate_phone_resp.status_code == 200
    assert duplicate_phone_resp.get_json()["code"] == 201

    duplicate_name_resp = client.post(
        "/register",
        data={"username": "registered_name", "phone": "13800000011", "password": "pass123"},
    )
    assert duplicate_name_resp.status_code == 200
    assert duplicate_name_resp.get_json()["code"] == 202


def test_consume_requires_login_and_balance(client):
    with app.app_context():
        _create_movie(brief_id=1001, price=15.0)
        _create_user(phone="13800000001", username="buyer", balance=5.0)

    not_login_resp = client.post("/consume", data={"movie_brief_id": "consume_1001"})
    assert not_login_resp.status_code == 200
    assert not_login_resp.get_json()["code"] == 301

    client.post("/login", data={"phone": "13800000001", "password": "pass123"})
    insufficient_resp = client.post("/consume", data={"movie_brief_id": "consume_1001"})
    assert insufficient_resp.status_code == 200
    assert insufficient_resp.get_json()["code"] == 302

    with app.app_context():
        buyer = User.query.filter_by(phone_number="13800000001").first()
        buyer.balance = 30.0
        db.session.add(buyer)
        db.session.add(ChargeRecord(user=buyer, money=25.0))
        db.session.commit()

    success_resp = client.post("/consume", data={"movie_brief_id": "consume_1001"})
    assert success_resp.status_code == 200
    assert success_resp.get_json()["code"] == 300

    with app.app_context():
        assert ConsumeRecord.query.count() == 1
        buyer = User.query.filter_by(phone_number="13800000001").first()
        assert buyer.balance == pytest.approx(15.0)

    duplicate_consume = client.post("/consume", data={"movie_brief_id": "consume_1001"})
    assert duplicate_consume.status_code == 200
    assert duplicate_consume.get_json()["code"] == 306


def test_consume_parameter_and_not_found_validation(client):
    with app.app_context():
        _create_user(phone="13800000021", username="consume_user", balance=30.0)

    client.post("/login", data={"phone": "13800000021", "password": "pass123"})

    bad_param_resp = client.post("/consume", data={"movie_brief_id": ""})
    assert bad_param_resp.status_code == 200
    assert bad_param_resp.get_json()["code"] == 303

    not_found_resp = client.post("/consume", data={"movie_brief_id": "consume_9999"})
    assert not_found_resp.status_code == 200
    assert not_found_resp.get_json()["code"] == 304
