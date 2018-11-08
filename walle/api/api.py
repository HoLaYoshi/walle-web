# -*- coding: utf-8 -*-
"""
    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2017-06-14 16:00:23
    :author: wushuiyong@walle-web.io
"""

from flask import jsonify, abort
from flask_login import login_required
from flask_restful import Resource
from walle.service.rbac.access import Access as AccessRbac
from walle.model.user import load_user

from functools import wraps

from flask import current_app, session
from flask_login import current_user

class ApiResource(Resource):
    module = None
    controller = None
    actions = None

    # TODO 权限验证
    # def __init__(self):
    #
    #     from walle.model.user import UserModel
    #     from flask_login import login_user
    #     from flask_login import current_user
    #     from flask import current_app
    #     user = UserModel.query.filter_by(email='wushuiyong@renrenche.com').first()
    #     # current_app.logger.info(__name__)
    #     # current_app.logger.info('islogin %s' % (current_user.is_authenticated))
    #     # current_app.logger.info('login_developer_user')
    #     # current_app.logger.info(user)
    #     # current_app.logger.info('role_id %s' % (dir(current_user)))
    #     # current_app.logger.info('role_id %s' % (current_user.role_info))
    #     login_user(user)
    #     # user_id => space_id
    #     session['space_id'] = 3
    #     session['group_id'] = 1
    #     current_user.space_id = 3
    #     current_user.role_name = 'master'
    #     current_app.logger.info('current_user space_id %s' % (current_user.space_id))
    #     # current_app.logger.info('islogin %s' % (current_user.is_authenticated))


    @staticmethod
    def render_json(code=0, message='', data=[]):
        return jsonify({
            'code': code,
            'message': message,
            'data': data,
        })

    @staticmethod
    def json(code=0, message=None, data=[]):
        return jsonify({
            'code': code,
            'message': message,
            'data': data,
        })

    @staticmethod
    def list_json(list, count, table={}, code=0, message='', enable_create=False):
        return ApiResource.render_json(data={'list': list, 'count': count, 'table': table, 'enable_create': enable_create},
                                       code=code,
                                       message=message)


class SecurityResource(ApiResource):
    module = None
    controller = None
    action = None

    #@login_required
    def get(self, *args, **kwargs):
        self.action = 'get'

        return self.validator()

    #@login_required
    def delete(self, *args, **kwargs):
        self.action = 'delete'
        is_allow = AccessRbac.is_allow(action=self.action, controller=self.controller)
        if not is_allow:
            self.render_json(code=403, message=u'无操作权限')
            # abort(403)
            pass
        pass

    #@login_required
    def put(self, *args, **kwargs):
        self.action = 'put'
        is_allow = AccessRbac.is_allow(action=self.action, controller=self.controller)
        if not is_allow:
            self.render_json(code=403, message=u'无操作权限')
            # abort(403)
            pass
        pass

    #@login_required
    def post(self, *args, **kwargs):
        """
        # @login_required
        :param args:
        :param kwargs:
        :return:
        """
        self.action = 'post'
        return self.validator()

    def validator(self):
        if not AccessRbac.is_login():
            return self.render_json(code=1000, message=u'请先登录')

        if not AccessRbac.is_allow(action=self.action, controller=self.controller):
            return self.render_json(code=1001, message=u'无操作权限')


    @staticmethod
    def is_super(func):
        @wraps(func)
        def is_enable(*args, **kwargs):
            # current_app.logger.info(dir(current_user.role_info))
            if current_user.role_info.name <> 'super':
                return ApiResource.render_json(code=403, message=u'无操作权限')
            current_app.logger.info("user is login: %s" % (current_user.is_authenticated))
            current_app.logger.info("args: %s kwargs: %s" % (args, kwargs))
            return func(*args, **kwargs)

        return is_enable

    @staticmethod
    def is_master(func):
        @wraps(func)
        def is_enable(*args, **kwargs):
            current_app.logger.info(dir(current_user.role_info))
            current_app.logger.info(current_user.role_info)
            if current_user.role_info.name not in ['super', 'master']:
                return ApiResource.render_json(code=403, message=u'无操作权限')
            current_app.logger.info("user is login: %s" % (current_user.is_authenticated))
            current_app.logger.info("args: %s kwargs: %s" % (args, kwargs))
            return func(*args, **kwargs)

        return is_enable

class Base(Resource):
    def get(self):
        """
        fetch role list or one role

        :return:
        """
        return 'walle-web 2.0'
