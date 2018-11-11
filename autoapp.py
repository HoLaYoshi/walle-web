# -*- coding: utf-8 -*-
"""Create an application instance."""
import sys

from flask.helpers import get_debug_flag
from walle.app import create_app
from walle.config.settings_dev import DevConfig
from walle.config.settings_test import TestConfig
from walle.config.settings_prod import ProdConfig

CONFIG = DevConfig if get_debug_flag(default=True) else ProdConfig

# from flask_login import current_user

if len(sys.argv) > 2 and sys.argv[2] == 'test':
    CONFIG = TestConfig

app = create_app(CONFIG)

app.logger.info('============ @app created ============')

@app.before_request
def before_request():
    app.logger.info('============ @app.before_request ============')
    from walle.model.user import UserModel
    from flask_login import login_user
    from flask_login import current_user
    from flask import current_app
    f = open('/Users/wushuiyong/workspace/meolu/walle_develop/run.logg', 'w')
    # user = UserModel.query.filter_by(email='wushuiyong@renrenche.com').first()
    # current_app.logger.info('islogin %s' % (current_user.is_authenticated))
    # current_app.logger.info('login_developer_user')
    f.write('before_request ')
    f.write('login_developer_user')
    f.close()
    # current_app.logger.info(user)
    # login_user(user)
    # current_app.logger.info('islogin %s' % (current_user.is_authenticated))
@app.teardown_request
def shutdown_session(exception=None):
    app.logger.info('============ @app.teardown_request ============')