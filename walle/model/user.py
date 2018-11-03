#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: wushuiyong
# @Created Time : 日  1/ 1 23:43:12 2017
# @Description:

from flask_login import UserMixin
from sqlalchemy import String, Integer, DateTime, or_
from werkzeug.security import check_password_hash, generate_password_hash

# from flask_cache import Cache
from datetime import datetime
from walle.service.extensions import login_manager
from walle.model.database import SurrogatePK, db, Model
from walle.model.tag import TagModel
from sqlalchemy.orm import aliased
from walle.service.rbac.access import Access as AccessRbac
from flask import current_app


class UserModel(UserMixin, SurrogatePK, Model):
    # 表的名字:
    __tablename__ = 'users'
    status_active  = 1
    status_blocked = 2

    current_time = datetime.now()
    password_hash = 'sadfsfkk'
    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    username = db.Column(String(50))
    is_email_verified = db.Column(Integer, default=0)
    email = db.Column(String(50), unique=True, nullable=False)
    password = db.Column(String(50), nullable=False)
    avatar = db.Column(String(100))
    status = db.Column(Integer, default=1)
    # role_info = relationship("walle.model.user.RoleModel", back_populates="users")
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    status_mapping = {
        0: '新建',
        1: '正常',
        2: '冻结',
    }

    def item(self, user_id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        data = self.query.filter_by(id=self.id).first()
        return data.to_json() if data else []

    def update(self, username, password=None):
        # todo permission_ids need to be formated and checked
        user = self.query.filter_by(id=self.id).first()
        user.username = username
        if password:
            user.password = generate_password_hash(password)

        db.session.commit()
        return user.to_json()

    def block_active(self, status):
        user = self.query.filter_by(id=self.id).first()
        user.status = status
        db.session.commit()
        return user.to_json()

    def remove(self):
        """

        :param role_id:
        :return:
        """
        self.query.filter_by(id=self.id).update({'status': self.status_remove})
        return db.session.commit()

    def verify_password(self, password):
        """
        检查密码是否正确
        :param password:
        :return:
        """
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    def set_password(self, password):
        """Set password."""
        self.password = generate_password_hash(password)

    def general_password(self, password):
        """
        检查密码是否正确
        :param password:
        :return:
        """
        self.password = generate_password_hash(password)
        return generate_password_hash(password)

    def fetch_access_list_by_role_id(self, role_id):
        module = aliased(MenuModel)
        controller = aliased(MenuModel)
        action = aliased(MenuModel)
        role = RoleModel.query.get(role_id)
        access_ids = role.access_ids.split(',')

        data = db.session \
            .query(controller.name_en, controller.name_cn,
                   action.name_en, action.name_cn) \
            .outerjoin(action, action.pid == controller.id) \
            .filter(module.type == MenuModel.type_module) \
            .filter(controller.id.in_(access_ids)) \
            .filter(action.id.in_(access_ids)) \
            .all()

        return [AccessRbac.resource(a_en, c_en) for c_en, c_cn, a_en, a_cn in data if c_en and a_en]

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        query = UserModel.query.filter(UserModel.status.notin_([self.status_remove]))
        if kw:
            query = query.filter(or_(UserModel.username.like('%' + kw + '%'), UserModel.email.like('%' + kw + '%')))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()
        user_list = [p.to_json() for p in data]
        return user_list, count

    @classmethod
    def fetch_by_uid(cls, uids=None):
        """
        用户列表
        :param uids: []
        :return:
        """
        if not uids:
            return None

        query = UserModel.query.filter(UserModel.id.in_(uids))
        data = query.order_by('id desc').all()
        return [p.to_json() for p in data]

    @classmethod
    def uid2name(cls, data):
        """
        把uid转换成名字
        :param data: [{'user_id':1, 'xx':'yy'}] 至少包含user_id
        :return:
        """
        user_ids = []
        uid2name = {}
        for items in data:
            user_ids.append(items.user_id)
        user_info = cls.fetch_by_uid(uids=user_ids)

        for user in user_info:
            uid2name[user['id']] = user['username']
        return uid2name

    def to_json(self):
        return {
            'id': int(self.id),
            'user_id': int(self.id),
            'username': self.username,
            'is_email_verified': self.is_email_verified,
            'email': self.email,
            'avatar': self.avatar,
            # TODO 当前登录用户的空间
            # 'role_id': self.role_id,
            'status': self.status_mapping[self.status],
            # 'status': self.status,
            # 'role_name': self.role_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class MenuModel(SurrogatePK, Model):
    __tablename__ = 'menus'

    type_module = 'module'
    type_controller = 'controller'
    type_action = 'action'

    status_open = 1
    status_close = 2
    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name_cn = db.Column(String(30))
    name_en = db.Column(String(30))
    pid = db.Column(Integer)
    type = db.Column(String(30))
    sequence = db.Column(Integer)
    archive = db.Column(Integer)
    icon = db.Column(String(30))
    url = db.Column(String(30))
    visible = db.Column(Integer)
    role = db.Column(Integer)
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    def menu(self, role):
        data = {}
        filters = {
             MenuModel.visible == 1,
             MenuModel.role >= role
        }
        query = self.query \
            .filter(*filters) \
            .order_by('sequence asc') \
            .all()
        for item in query:
            if item.type == self.type_module:
                module = {
                    'title': item.name_cn,
                    'icon': item.icon,
                    'sub_menu': [],
                }
                if item.url:
                    module['url'] = item.url
                data[item.id] = module
            elif item.type == self.type_controller:
                data[item.pid]['sub_menu'].append({
                    'title': item.name_cn,
                    'icon': item.icon,
                    'url': item.url,
                })

        return data.values()

    def list(self):
        """
        获取分页列表
        :param page:
        :param size:
        :param kw:
        :return:
        """
        menus_module = {}
        menus_controller = {}
        module = aliased(MenuModel)
        controller = aliased(MenuModel)
        action = aliased(MenuModel)

        data = db.session.query(module.id, module.name_cn, controller.id, controller.name_cn, action.id, action.name_cn) \
            .outerjoin(controller, controller.pid == module.id) \
            .outerjoin(action, action.pid == controller.id) \
            .filter(module.type == self.type_module) \
            .all()
        for m_id, m_name, c_id, c_name, a_id, a_name in data:
            # module
            if not menus_module.has_key(m_id):
                menus_module[m_id] = {
                    'id': m_id,
                    'title': m_name,
                    'sub_menu': {},
                }
            # controller
            if not menus_module[m_id]['sub_menu'].has_key(c_id) and c_name:
                menus_module[m_id]['sub_menu'][c_id] = {
                    'id': c_id,
                    'title': c_name,
                    'sub_menu': {},
                }
            # action
            if not menus_controller.has_key(c_id):
                menus_controller[c_id] = []
            if a_name:
                menus_controller[c_id].append({
                    'id': a_id,
                    'title': a_name,
                })
        menus = []
        for m_id, m_info in menus_module.items():
            for c_id, c_info in m_info['sub_menu'].items():
                m_info['sub_menu'][c_id]['sub_menu'] = menus_controller[c_id]
            menus.append({
                'id': m_id,
                'title': m_info['title'],
                'sub_menu': m_info['sub_menu'].values(),
            })

        return menus

    def to_json(self):
        return {
            'id': self.id,
            'name_cn': self.name_cn,
            'name_en': self.name_en,
            'pid': self.pid,
            'type': self.type,
            'sequence': self.sequence,
            'archive': self.archive,
            'icon': self.icon,
            'url': self.url,
            'visible': self.visible,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class RoleModel(object):
    _role_super = 'SUPER'

    _role_owner = 'OWNER'

    _role_master = 'MASTER'

    _role_developer = 'DEVELOPER'

    _role_reporter = 'REPORTER'

    @classmethod
    def list(cls):
        roles = [
            {'id': cls._role_super, 'name': '超级管理员'},
            {'id': cls._role_owner, 'name': '空间所有者'},
            {'id': cls._role_master, 'name': '项目管理员'},
            {'id': cls._role_developer, 'name': '开发者'},
            {'id': cls._role_reporter, 'name': '访客'},
        ]
        return roles, len(roles)

    @classmethod
    def item(cls, role_id):
        return None


# 项目配置表
class MemberModel(SurrogatePK, Model):
    __tablename__ = 'members'

    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, db.ForeignKey('users.id'))
    source_id = db.Column(Integer)
    source_type = db.Column(Integer)
    access_level = db.Column(Integer)
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)
    group_name = None

    def list(self):
        pass



# 项目配置表
class GroupModel(SurrogatePK, Model):
    __tablename__ = 'user_group'

    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, db.ForeignKey('users.id'))
    # TODO
    # user_ids = db.relationship('walle.model.tag.TagModel', backref=db.backref('users'))
    group_id = db.Column(Integer, db.ForeignKey('tags.id'))
    project_id = db.Column(Integer, db.ForeignKey('projects.id'))
    role = db.Column(String(30))
    status = db.Column(Integer)
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)
    group_name = None

    # TODO group id全局化

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        group = GroupModel.query.filter(GroupModel.status.notin_([self.status_remove]))
        if kw:
            group = group.filter_by(TagModel.name.like('%' + kw + '%'))
        group = group.offset(int(size) * int(page)).limit(size).all()

        list = [p.to_json() for p in group]
        return list, 3

        user_ids = []
        group_dict = {}
        for group_info in group:
            user_ids.append(group_info.user_id)
            group_dict = group_info.to_json()

        group_dict['user_ids'] = user_ids
        # del group_dict['user_id']
        # return user_ids
        return group_dict

        query = TagModel.query
        if kw:
            query = query.filter(TagModel.name.like('%' + kw + '%'))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()
        list = [p.to_json() for p in data]
        return list, count

    def add(self, space_name, members):
        """

        :param space_name:
        :param members: [{'user_id': 1, 'project_id': 2}]
        :return:
        """
        tag = TagModel(name=space_name, label='user_group')
        db.session.add(tag)
        db.session.commit()
        current_app.logger.info(members)

        for member in members:
            user_group = GroupModel(group_id=tag.id, user_id=member['user_id'], project_id=member['project_id'])
            db.session.add(user_group)

        db.session.commit()
        if tag.id:
            self.group_id = tag.id

        return tag.id

    def update_group(self, members, group_name=None):
        current_app.logger.info(members)
        # 修改tag信息
        if group_name:
            tag_model = TagModel.query.filter_by(label='user_group').filter_by(id=self.group_id).first()
            if tag_model.name != group_name:
                tag_model.name = group_name

        # 修改用户组成员
        # clean up
        GroupModel.query.filter_by(group_id=self.group_id).delete()

        # insert all
        for member in members:
            tag = GroupModel(user_id=member['user_id'], group_id=self.group_id, role=member['role'])
            db.session.add(tag)

        db.session.commit()
        return self.item()

    def update_project(self, project_id, members, group_name=None):
        group_model = self.item()
        user_update = []

        current_app.logger.info(members)
        for member in members:
            user_update.append(member['user_id'])

        # project新增用户是否在space's group中,无则抛出
        if list(set(user_update).difference(set(group_model['user_ids']))):
            raise ValueError('用户不存在')

        # 修改用户组成员
        # clean up
        GroupModel.query.filter_by(project_id=project_id).delete()

        # insert all
        for member in members:
            group = GroupModel(user_id=member['user_id'], group_id=self.group_id, project_id=project_id, role=member['role'])
            db.session.add(group)

        return db.session.commit()

    def item(self, group_id=None, project_id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        #
        group_id = group_id if group_id else self.group_id
        tag = TagModel.query.filter_by(id=group_id).first()
        if not tag:
            return None
        tag = tag.to_json()

        group_id = group_id if group_id else self.group_id
        query = GroupModel.query.filter_by(group_id=group_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        groups = query.all()

        user_ids = []
        user_role = {}
        for group_info in groups:
            user_ids.append(group_info.user_id)
            user_role[group_info.user_id] = group_info.role

        current_app.logger.info(user_ids)
        user_model = UserModel()
        user_info = user_model.fetch_by_uid(uids=set(user_ids))
        # current_app.logger.info(user_info)
        if user_info:
            for user in user_info:
                if user_role.has_key(user['id']):
                    user['role'] = user_role[user['id']]


        tag['user_ids'] = user_ids
        tag['members'] = user_info
        tag['users'] = len(user_ids)
        return tag

        del group_dict['user_id']
        # return user_ids
        return group_dict
        return group.to_json()
        # group = group.to_json()

        users = UserModel.query \
            .filter(UserModel.id.in_(group['users'])).all()
        group['user_ids'] = [user.to_json() for user in users]

        return group

    def remove(self, group_id=None, user_id=None, project_id=None):
        """

        :param role_id:
        :return:
        """
        if group_id:
            GroupModel.query.filter_by(group_id=group_id).update({'status': self.status_remove})
        elif user_id:
            GroupModel.query.filter_by(user_id=user_id).update({'status': self.status_remove})
        elif self.group_id:
            GroupModel.query.filter_by(group_id=self.group_id).update({'status': self.status_remove})
        elif project_id:
            GroupModel.query.filter_by(project_id=project_id).update({'status': self.status_remove})

        return db.session.commit()

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'group_name': self.group_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


# 项目配置表
class SpaceModel(SurrogatePK, Model):
    # 表的名字:
    __tablename__ = 'spaces'
    current_time = datetime.now()
    status_close = 0
    status_open = 1

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer)
    group_id = db.Column(Integer)
    name = db.Column(String(100))
    status = db.Column(Integer)

    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        query = self.query.filter(SpaceModel.status.notin_([self.status_remove]))
        if kw:
            query = query.filter(SpaceModel.name.like('%' + kw + '%'))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()

        uid2name = UserModel.uid2name(data=data)
        list = [p.to_json(uid2name) for p in data]
        return list, count

    def item(self, id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        id = id if id else self.id
        # data = self.query.filter_by(id=id).first()

        return GroupModel(group_id=id).item()

        if not data:
            return []

        data = data.to_json()

        return data

    def add(self, *args, **kwargs):
        # todo permission_ids need to be formated and checked
        data = dict(*args)

        tag = TagModel(name=data['name'], label='user_group')
        db.session.add(tag)
        db.session.commit()

        user_group = GroupModel(group_id=tag.id, user_id=data['user_id'])
        db.session.add(user_group)
        db.session.commit()

        data['group_id'] = tag.id
        space = SpaceModel(**data)

        db.session.add(space)
        db.session.commit()
        self.id = space.id

        return self.id

    def update(self, *args, **kwargs):
        # todo permission_ids need to be formated and checked
        # a new type to update a model

        update_data = dict(*args)
        return super(SpaceModel, self).update(**update_data)

    def remove(self, space_id=None):
        """

        :param space_id:
        :return:
        """
        space_id = space_id if space_id else self.id
        SpaceModel.query.filter_by(id=space_id).update({'status': self.status_remove})
        return db.session.commit()

    def to_json(self, uid2name=None):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': uid2name[self.user_id] if uid2name and uid2name.has_key(self.user_id) else '',
            'group_id': self.group_id,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


@login_manager.user_loader
def load_user(user_id):
    # user = UserModel.query.get(user_id)
    # role = RoleModel().item(user.role_id)
    # access = UserModel().fetch_access_list_by_role_id(user.role_id)
    # logging.error(RoleModel.query.get(user.role_id).access_ids)
    # logging.error(role['access_ids'].split(','))
    # logging.error(UserModel.query.get(user_id))
    return UserModel.query.get(user_id)
