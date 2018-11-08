# -*- coding: utf-8 -*-
"""
    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2018-11-04 22:08:28
    :author: wushuiyong@walle-web.io
"""


GUEST = 'GUEST'
REPORT = 'REPORT'
DEVELOPER = 'DEVELOPER'
MASTER = 'MASTER'
OWNER = 'OWNER'
SUPER = 'SUPER'

ACCESS_ROLE = {
    '10': GUEST,
    '20': REPORT,
    '30': DEVELOPER,
    '40': MASTER,
    '50': OWNER,
    '60': SUPER,
}

ROLE_ACCESS = {
    'GUEST': '10',
    'REPORT': '20',
    'DEVELOPER': '30',
    'MASTER': '40',
    'OWNER': '50',
    'SUPER': '60',
}

class Permission():

    @staticmethod
    def list_enable(self, list, access_level):
        current_role = OWNER
        access_level = {
            'create': OWNER,
            'update': MASTER,
            'delete': MASTER,
            'online': DEVELOPER,
            'audit': MASTER,
            'block': DEVELOPER,
        }
        # 1 uid == current_uid && access_level >= current_role
        #       all true
        # uid, project_id, space_id

        return {
            'enable_create': OWNER,
            'enable_update': MASTER,
            'enable_delete': MASTER,
            'enable_online': DEVELOPER,
            'enable_audit': MASTER,
            'enable_block': DEVELOPER,
        }
        pass

    @classmethod
    def enable_uid(cls, uid):
        '''
        当前登录用户 == 数据用户
        :param uid:
        :return:
        '''
        return True

    @classmethod
    def enable_role(cls, role):
        '''
        当前角色 > 数据项角色
        :param role:
        :return:
        '''
        current_role = SUPER
        return cls.compare_role(current_role, role)

    @classmethod
    def compare_role(cls, role_high, role_low):
        if role_high not in ROLE_ACCESS or role_low not in ROLE_ACCESS:
            # TODO 也可以抛出
            return False

        return ROLE_ACCESS[role_high] > ROLE_ACCESS[role_low]