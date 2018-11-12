# -*- coding: utf-8 -*-
"""
    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2018-11-11 19:49:37
    :author: wushuiyong@walle-web.io
"""


class Code():

    #: 1xxx 表示用户相关: 登录, 权限
    #: 未登录, 大概是永远不会变了
    unlogin = 1000

    not_allow = 1001


    #: 2xxx 表示参数错误
    params_error = 2000


    code_msg = {
        unlogin: '未登录',
        not_allow: '无此权限',
        params_error: '参数错误',
    }


