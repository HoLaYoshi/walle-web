# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys, os

from flask import Flask, render_template
from flask_restful import Api
from tornado.ioloop import IOLoop
from tornado.web import Application, FallbackHandler
from tornado.wsgi import WSGIContainer
from walle import commands
from walle.api import access as AccessAPI
from walle.api import api as BaseAPI
from walle.api import deploy as DeployAPI
from walle.api import environment as EnvironmentAPI
from walle.api import group as GroupAPI
from walle.api import passport as PassportAPI
from walle.api import project as ProjectAPI
from walle.api import general as GeneralAPI
from walle.api import role as RoleAPI
from walle.api import server as ServerAPI
from walle.api import task as TaskAPI
from walle.api import user as UserAPI
from walle.api import space as SpaceAPI
from walle.api import repo as RepoApi
from walle.config.settings_dev import DevConfig
from walle.config.settings_test import TestConfig
from walle.config.settings_prod import ProdConfig
from walle.model.user import UserModel
from walle.service.extensions import bcrypt, csrf_protect, db, migrate
from walle.service.extensions import login_manager, mail
from walle.service.websocket import WSHandler


# TODO 添加到这,则对单测有影响
app = Flask(__name__.split('.')[0])


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    # app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    register_logging(app)

    # app.logger.info('=== testing ===')

    # 测试环境跑单测失败
    if not app.config['TESTING']:
        register_websocket(app)

    register_websocket(app)

    reload(sys)
    sys.setdefaultencoding('utf-8')
    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    api = Api(app)
    api.add_resource(BaseAPI.Base, '/', endpoint='root')
    api.add_resource(GeneralAPI.GeneralAPI, '/api/general/<string:action>', endpoint='general')
    api.add_resource(SpaceAPI.SpaceAPI, '/api/space/', '/api/space/<int:space_id>', endpoint='space')
    api.add_resource(DeployAPI.DeployAPI, '/api/deploy/', '/api/deploy/<int:task_id>', endpoint='deploy')
    api.add_resource(AccessAPI.AccessAPI, '/api/access/', '/api/access/<int:access_id>', endpoint='access')
    api.add_resource(RoleAPI.RoleAPI, '/api/role/', endpoint='role')
    api.add_resource(GroupAPI.GroupAPI, '/api/group/', '/api/group/<int:group_id>', endpoint='group')
    api.add_resource(PassportAPI.PassportAPI, '/api/passport/', '/api/passport/<string:action>', endpoint='passport')
    api.add_resource(UserAPI.UserAPI, '/api/user/', '/api/user/<string:action>', '/api/user/<int:user_id>', endpoint='user')
    api.add_resource(ServerAPI.ServerAPI, '/api/server/', '/api/server/<int:id>', endpoint='server')
    api.add_resource(ProjectAPI.ProjectAPI, '/api/project/', '/api/project/<int:project_id>', '/api/project/<int:project_id>/<string:action>', endpoint='project')
    api.add_resource(RepoApi.RepoAPI, '/api/repo/<string:action>/', endpoint='repo')
    api.add_resource(TaskAPI.TaskAPI, '/api/task/', '/api/task/<int:task_id>', '/api/task/<int:task_id>/<string:action>', endpoint='task')
    api.add_resource(EnvironmentAPI.EnvironmentAPI, '/api/environment/', '/api/environment/<int:env_id>',
                     endpoint='environment')

    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': UserModel,
        }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def register_logging(app):
    # TODO https://blog.csdn.net/zwxiaoliu/article/details/80890136
    # email errors to the administrators
    import logging
    from logging.handlers import RotatingFileHandler
    # Formatter
    formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(pathname)s %(lineno)s %(module)s.%(funcName)s %(message)s')

    # log dir
    if not os.path.exists(app.config['LOG_PATH']):
        os.makedirs(app.config['LOG_PATH'])

    # FileHandler Info
    file_handler_info = RotatingFileHandler(filename=app.config['LOG_PATH_INFO'])
    file_handler_info.setFormatter(formatter)
    file_handler_info.setLevel(logging.INFO)
    info_filter = InfoFilter()
    file_handler_info.addFilter(info_filter)
    app.logger.addHandler(file_handler_info)

    # FileHandler Error
    file_handler_error = RotatingFileHandler(filename=app.config['LOG_PATH_ERROR'])
    file_handler_error.setFormatter(formatter)
    file_handler_error.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler_error)


def register_websocket(app):
    settings = {'debug': True}

    # TODO fix websocket app_context
    ctx = app.app_context()
    ctx.push()

    wsgi_app = WSGIContainer(app)

    application = Application([
        (r'/websocket/console', WSHandler),
        (r'.*', FallbackHandler, dict(fallback=wsgi_app))
    ], **settings)

    application.listen(5000)
    IOLoop.instance().start()
    pass


class InfoFilter(logging.Filter):
    def filter(self, record):
        """only use INFO
        筛选, 只需要 INFO 级别的log
        :param record:
        :return:
        """
        if logging.INFO <= record.levelno < logging.ERROR:
            # 已经是INFO级别了
            # 然后利用父类, 返回 1
            return 1
        else:
            return 0

# TODO optimize
@app.route('/api/websocket')
def index():

    return render_template('websocket.html')
