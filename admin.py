#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from markupsafe import Markup

from app import app

from models import db
from models import User, Movie, MoviePrice, ConsumeRecord, ChargeRecord, Comment


class UserView(ModelView):
    can_delete = True
    can_edit = False
    can_create = False
    can_view_details = True

    column_labels = dict(
        id='ID',
        username='用户名',
        password_hash='密码',
        phone_number='电话',
        avatar='头像',
        balance='余额',
    )

    def _avatar(view, context, model, name):
        if model.avatar:
            return Markup('<img src="{}">'.format(model.avatar))

    column_formatters = dict(
        avatar=_avatar,
    )

    column_display_pk = True

    column_searchable_list = (
        'username',
        'phone_number',

    )

    column_exclude_list = (
        'password_hash'
    )


class CommentView(ModelView):
    can_delete = True
    can_edit = False
    can_create = False
    can_view_details = True

    column_labels = dict(
        id='ID',
        from_user='用户',
        movie='电影',
        comment_time='评论时间',
        content='评论内容',
        point='评分',
    )

    column_exclude_list = (
        'to_user'
    )


class MovieView(ModelView):
    can_create = False
    can_view_details = True

    column_labels = dict(
        title='电影',
        price='价格',
        brief_id='短ID',
        cover='海报',
        info='信息',
        summary='剧情简介',
        video_uri='视频地址',
    )

    form_columns = (
        'title',
        'brief_id',
        'cover',
        'info',
        'summary',
        'video_uri',
    )

    def _cover(view, context, model, name):
        if model.cover:
            return Markup('<img src="{}">'.format(model.cover))

    def _video_uri(view, context, model, name):
        if model.video_uri:
            return Markup('<a hre="{}">'.format(model.video_uri))

    def _info(view, context, model, name):
        if model.info:
            return model.info[0:20]

    def _summary(view, context, model, name):
        if model.summary:
            return model.summary[0:40]

    column_formatters = dict(
        cover=_cover,
        info=_info,
        summary=_summary,
        video_uri=_video_uri,
    )

    column_display_pk = False


class MoviePriceView(ModelView):
    can_create = False

    column_labels = dict(
        movie='电影',
        price='价格',
    )


class ConsumeRecordview(ModelView):
    can_create = False
    can_edit = False
    can_view_details = True

    column_labels = dict(
        consume_time='购买时间',
        movie='电影',
        money='金额',
        consumer='用户',
    )


class ChargeRecordView(ModelView):
    can_create = False
    can_edit = False
    can_view_details = True

    column_labels = dict(
        charge_time='充值',
        money='金额',
        user='用户',
    )

    column_searchable_list = []


admin = Admin(app, name='电影船后台管理')

admin.add_view(UserView(User, db.session, name='用户'))
admin.add_view(MovieView(Movie, db.session, name='电影'))
admin.add_view(CommentView(Comment, db.session, name='用户评论'))
admin.add_view(MoviePriceView(MoviePrice, db.session, name='价格'))
admin.add_view(ConsumeRecordview(ConsumeRecord, db.session, name='购买记录'))
admin.add_view(ChargeRecordView(ChargeRecord, db.session, name='充值记录'))
