# -*- coding: utf-8 -*-
"""

    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2017-03-25 11:15:01
    :author: wushuiyong@walle-web.io
"""
import os
from flask import request, current_app, abort
from walle.api.api import SecurityResource
from walle.form.user import UserUpdateForm, RegistrationForm
from walle.model.database import db
from walle.model.user import GroupModel
from walle.model.user import UserModel
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import current_user

class UserAPI(SecurityResource):

    actions = ['avater', 'block', 'active']

    def get(self, user_id=None, method=None):
        """
        fetch user list or one user
        /user/<int:user_id>

        :return:
        """
        super(UserAPI, self).get()

        return self.item(user_id) if user_id else self.list()


    def list(self):
        """
        fetch user list or one user

        :return:
        """
        page = int(request.args.get('page', 0))
        page = page - 1 if page else 0
        size = float(request.args.get('size', 10))
        kw = request.values.get('kw', '')

        user_model = UserModel()
        user_list, count = user_model.list(page=page, size=size, kw=kw)
        filter = {
            'username': ['线上', '线下'],
            'status': ['正常', '禁用']
        }
        return self.list_json(list=user_list, count=count, table=self.table(filter))

    def item(self, user_id):
        """
        获取某个用户

        :param user_id:
        :return:
        """

        user_info = UserModel(id=user_id).item()
        if not user_info:
            return self.render_json(code=-1)
        return self.render_json(data=user_info)

    def post(self):
        """
        create user
        /user/

        :return:
        """
        super(UserAPI, self).post()

        form = RegistrationForm(request.form, csrf_enabled=False)
        if form.validate_on_submit():
            password = generate_password_hash(form.password.data)
            user = UserModel(email=form.email.data,
                             username=form.username.data,
                             password=password,
                             )
            db.session.add(user)
            db.session.commit()
            return self.render_json(data=user.item(user_id=user.id))
        return self.render_json(code=-1, message=form.errors)

    def put(self, user_id, action=None):
        """
        edit user
        /user/<int:user_id>

        :return:
        """
        super(UserAPI, self).put()

        if action:
            if action in self.actions:
                self_action = getattr(self, action.lower(), None)
                return self_action(user_id=user_id)
            else:
                abort(404)

        form = UserUpdateForm(request.form, csrf_enabled=False)
        if form.validate_on_submit():
            user = UserModel(id=user_id)
            user.update(username=form.username.data, password=form.password.data)
            return self.render_json(data=user.item())

        return self.render_json(code=-1, message=form.errors)

    def delete(self, user_id):
        """
        remove a user with his group relation
        /user/<int:user_id>

        :param user_id:
        :return:
        """
        super(UserAPI, self).delete()

        UserModel(id=user_id).remove()
        GroupModel().remove(user_id=user_id)
        return self.render_json(message='')

    def table(self, filter={}):
        table = {
            'username': {
                'sort': 0
            },
            'email': {
                'sort': 0
            },
            'status': {
                'sort': 0
            },
            'role_name': {
                'sort': 0
            },
        }
        ret = []
        for (key, value) in table.items():
            value['key'] = key
            if key in filter:
                value['value'] = filter[key]
            else:
                value['value'] = []
            ret.append(value)
        return ret

    def avater(self, user_id):
        # TODO uid
        # fname = current_user.id + '.jpg'

        UPLOAD_FOLDER = 'fe/public/avater'
        f = request.files['avater']
        # todo rename to uid relation
        fname = secure_filename(f.filename)
        ret = f.save(os.path.join(current_app.config['UPLOAD_AVATER'], fname))

        return self.render_json(data={
            'avarter': str(request.args),
            'u': dir(current_user),
        })

    def block(self, user_id):
        user = UserModel(id=user_id)
        user.block_active(UserModel.status_blocked)
        return self.render_json(data=user.item())

    def active(self, user_id):
        user = UserModel(id=user_id)
        user.block_active(UserModel.status_active)
        return self.render_json(data=user.item())
