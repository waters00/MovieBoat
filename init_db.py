#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import random
import datetime
import math

from faker import Faker
import pymongo

from models import User, Movie, Comment, ChargeRecord, ConsumeRecord, MoviePrice, Reply
from models import db

fake = Faker('zh_CN')


def get_mongo_cursor():
    client = pymongo.MongoClient('docker')
    db = client['bt0_movie']

    cursor = db.bt0_movie.find()
    return cursor


def gen_users(amount=50):
    for i in range(amount):
        u = User(username=fake.name(), password='password')
        u.phone_number = fake.phone_number()
        u.avatar = 'http://opsfsk07z.bkt.clouddn.com/avatar-{}.jpg'.format(random.choice(range(50)))
        db.session.add(u)
        db.session.commit()


def get_movies():
    i = 1000
    for item in get_mongo_cursor():
        i += 1
        m = Movie(
            title=item['title'],
            cover=item['img'],
            info=item['info'],
            summary=item['summary'].lstrip(),
            brief_id=i,
            video_uri='http://oh6k349gl.bkt.clouddn.com/sample-001.mp4'
        )

        mp = MoviePrice(
            movie=m,
            price=math.floor(random.random() * 20)
        )

        db.session.add(m)
        db.session.add(mp)
        db.session.commit()


def gen_comments(amount=100):
    comments = [
        '太好看了！而且非常难得的是，电影并没有在经历DCEU几番口碑失败后向Y靠拢，反而是在扎克施耐德打下的原有主题基调下做的更好更成熟',
        '大家快跑啊骗钱的又来了',
        '本来以为正片就够尴尬了，没想到五个彩蛋更是尴尬到顶点',
        '太空电影可以不拍成一个人孤独战斗的缩影。无论多么绝望都剩下最后一点掐不灭的希望，这点太喜欢了，这种设定也很适合马特达蒙自身',
        'M工作室目前最棒的电影，没有之一，必看！比Y系列更上一个档次！ ',
        '过于浓重的说教意味，毫无逻辑的人物设定',
        '很棒，有史诗的感觉，画面感各方面都不错，特效也不错',
        '看完了，没有说的那么好看，情节上好多都比较牵强',
        '是我最喜欢的系列之一',
        '我料想过它好，可没想过居然这么好，一部电影，故事，角色，演员，情感，内涵，光影，剪辑的运用。',
        '能有一方面做好便已经难得，而它居然全部都做到了。',

    ]

    for i in range(amount):
        u = random.choice(User.query.all())
        m = random.choice(Movie.query.all())

        c = Comment(
            user=u,
            movie=m,
            comment_time=datetime.datetime.now() + datetime.timedelta(fake.random_digit()),
            content=random.choice(comments),
            point=random.choice(range(5)) + 1,
        )

        db.session.add(c)
        db.session.commit()

    gen_replies(amount)


def gen_replies(amount):
    for i in range(amount):
        replies = [
            '我觉得你说的没有道理',
            '说得太对了！',
            '本来以为正片就够尴尬了',
            '同感！',
            '强行挑缺点',
            '能有一方面做好便已经难得',
        ]

        if random.randint(0, 10) % 2 == 0:
            u = random.choice(User.query.all())
            to_comment = random.choice(Comment.query.all())
            reply = Reply(
                user=u,
                to_comment=to_comment,
                reply_time=datetime.datetime.now() + datetime.timedelta(fake.random_digit()),
                content=random.choice(replies),
            )

            db.session.add(reply)
            db.session.commit()


def gen_charge_records(amount=100):
    for i in range(amount):
        u = random.choice(User.query.all())
        money = math.floor(random.random() * 20)
        cr = ChargeRecord(
            user=u,
            charge_time=datetime.datetime.now() + datetime.timedelta(fake.random_digit()),
            money=money,
        )
        u.balance += money
        db.session.add(cr)
        db.session.add(u)
        db.session.commit()


def gen_consume_records(amount=100):
    for i in range(amount):
        u = random.choice(User.query.all())
        m = random.choice(Movie.query.all())

        u.balance += 75

        money = MoviePrice.query.get(m.id).price

        if u.balance > money:
            cr = ConsumeRecord(
                consumer=u,
                movie=m,
                consume_time=datetime.datetime.now() + datetime.timedelta(fake.random_digit()),
                money=money,
            )
            u.balance -= money
            db.session.add(cr)
            db.session.add(u)
            db.session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='你要初始化的表名')

    args = parser.parse_args()

    _mapper = {
        'user': gen_users,
        'movie': get_movies,
        'comment': gen_comments,
        'charge': gen_charge_records,
        'consume': gen_consume_records,
    }

    try:
        _mapper[args.name]()
    except KeyError:
        print("参数不合法")
