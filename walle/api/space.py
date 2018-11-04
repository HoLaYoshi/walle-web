# -*- coding: utf-8 -*-
"""

    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2017-03-25 11:15:01
    :author: wushuiyong@walle-web.io
"""

from flask import request, current_app
from walle.api.api import SecurityResource
from walle.form.space import SpaceForm
from walle.model.user import SpaceModel, MemberModel
import json

class SpaceAPI(SecurityResource):

    def get(self, space_id=None):
        """
        fetch space list or one item
        /space/<int:space_id>

        :return:
        """
        super(SpaceAPI, self).get()

        return self.item(space_id) if space_id else self.list()

    def list(self):
        """
        fetch space list

        :return:
        """
        page = int(request.args.get('page', 0))
        page = page - 1 if page else 0
        size = float(request.args.get('size', 10))
        kw = request.values.get('kw', '')

        space_model = SpaceModel()
        space_list, count = space_model.list(page=page, size=size, kw=kw)
        return self.list_json(list=space_list, count=count)

    def item(self, space_id):
        """
        获取某个用户组

        :param id:
        :return:
        """

        space_model = SpaceModel(id=space_id)
        space_info = space_model.item()
        if not space_info:
            return self.render_json(code=-1)
        return self.render_json(data=space_info)

    def post(self):
        """
        create a space
        /environment/

        :return:
        """
        super(SpaceAPI, self).post()

        form = SpaceForm(request.form, csrf_enabled=False)
        # return self.render_json(code=-1, data = form.form2dict())
        if form.validate_on_submit():
            # create space
            space_new = SpaceModel()
            data = form.form2dict()
            id = space_new.add(data)
            if not id:
                return self.render_json(code=-1)

            current_app.logger.info(request.json)
            # create group
            MemberModel(group_id=id).update_group(members=json.loads(request.form['members']))
            return self.render_json(data=space_new.item())
        else:
            return self.render_json(code=-1, message=form.errors)

    def put(self, space_id):
        """
        update environment
        /environment/<int:id>

        :return:
        """
        super(SpaceAPI, self).put()

        form = SpaceForm(request.form, csrf_enabled=False)
        form.set_id(space_id)
        if form.validate_on_submit():
            space = SpaceModel().get_by_id(space_id)
            data = form.form2dict()
            # a new type to update a model
            ret = space.update(data)
            # create group
            MemberModel(group_id=space_id).update_group(members=json.loads(request.form['members']))
            return self.render_json(data=space.item())
        else:
            return self.render_json(code=-1, message=form.errors)

    def delete(self, space_id):
        """
        remove an environment
        /environment/<int:id>

        :return:
        """
        super(SpaceAPI, self).delete()

        space_model = SpaceModel(id=space_id)
        space_model.remove(space_id)

        return self.render_json(message='')
