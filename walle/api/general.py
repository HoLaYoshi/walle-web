# -*- coding: utf-8 -*-
"""

    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2017-03-25 11:15:01
    :author: wushuiyong@walle-web.io
"""

import os
from flask import request, abort, session
from flask_login import current_user
from walle.api.api import ApiResource
from walle.model.deploy import TaskRecordModel
from walle.model.user import MenuModel
from walle.model.user import UserModel
from walle.service import emails
from walle.service.deployer import Deployer
from werkzeug.utils import secure_filename


class GeneralAPI(ApiResource):
    actions = ['menu', 'websocket']

    def get(self, action):
        """
        fetch role list or one role

        :return:
        """

        if action in self.actions:
            self_action = getattr(self, action.lower(), None)
            return self_action()
        else:
            abort(404)

    def post(self, action):
        """
        fetch role list or one role

        :return:
        """
        if action == 'avater':
            return self.avater()

    def menu(self):
        role = 10
        user = UserModel(id=1).item()
        menu = MenuModel().menu(role=role)
        # TODO
        space_id = 1
        if 'space_id' in session and session['space_id']:
            space_id = session['space_id']
        spaces = {
            1: {'id': 1, 'name': '大数据'},
            2: {'id': 2, 'name': '瓦力'},
            3: {'id': 3, 'name': '瓦尔登'}
        }
        space = spaces[space_id]
        del spaces[space_id]

        space = {
            'current': space,
            'available': list(spaces.values())
        }
        data = {
            'user': user,
            'menu': menu,
            'space': space,
        }
        return self.render_json(data=data)

    def avater(self):
        UPLOAD_FOLDER = 'fe/public/avater'
        f = request.files['avater']
        fname = secure_filename(f.filename)
        # todo rename to uid relation
        fname = secure_filename(f.filename)
        ret = f.save(os.path.join(UPLOAD_FOLDER, fname))

        return self.render_json(data={
            'avarter': fname,
        })

    def mail(self):
        ret = emails.send_email('wushuiyong@renrenche.com', 'email from service@walle-web.io', 'xxxxxxx', 'yyyyyyy')
        return self.render_json(data={
            'avarter': 'emails.send_email',
            'done': ret,
        })

    def websocket(self, task_id=None):
        task_id = 12
        wi = Deployer(task_id)
        ret = wi.walle_deploy()
        record = TaskRecordModel().fetch(task_id)
        return self.render_json(data={
            'command': ret,
            'record': record,
        })
