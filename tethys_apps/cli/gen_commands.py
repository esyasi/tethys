"""
********************************************************************************
* Name: gen_commands.py
* Author: Nathan Swain
* Created On: 2015
* Copyright: (c) Brigham Young University 2015
* License: BSD 2-Clause
********************************************************************************
"""
import os
import ast
import string
import random
from tethys_apps.utilities import get_tethys_home_dir, get_tethys_src_dir
from platform import linux_distribution

from django.template import Template, Context
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tethys_portal.settings")


# Initialize settings
try:
    __import__(os.environ['DJANGO_SETTINGS_MODULE'])
except Exception:
    # Initialize settings with templates variable to allow gen to work properly
    settings.configure(TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
        }
    ])
import django  # noqa: E402
django.setup()


__all__ = ['VALID_GEN_OBJECTS', 'generate_command']


GEN_SETTINGS_OPTION = 'settings'
GEN_APACHE_OPTION = 'apache'
GEN_ASGI_SERVICE_OPTION = 'asgi_service'
GEN_NGINX_OPTION = 'nginx'
GEN_NGINX_SERVICE_OPTION = 'nginx_service'
GEN_PORTAL_OPTION = 'portal'
GEN_SERVICES_OPTION = 'services'
GEN_INSTALL_OPTION = 'install'

FILE_NAMES = {GEN_SETTINGS_OPTION: 'settings.py',
              GEN_APACHE_OPTION: 'tethys-default.conf',
              GEN_ASGI_SERVICE_OPTION: 'asgi_supervisord.conf',
              GEN_NGINX_OPTION: 'tethys_nginx.conf',
              GEN_NGINX_SERVICE_OPTION: 'nginx_supervisord.conf',
              GEN_PORTAL_OPTION: 'portal.yml',
              GEN_SERVICES_OPTION: 'services.yml',
              GEN_INSTALL_OPTION: 'install.yml',
              }

VALID_GEN_OBJECTS = (GEN_SETTINGS_OPTION,
                     GEN_APACHE_OPTION,
                     GEN_ASGI_SERVICE_OPTION,
                     GEN_NGINX_OPTION,
                     GEN_NGINX_SERVICE_OPTION,
                     GEN_PORTAL_OPTION,
                     GEN_SERVICES_OPTION,
                     GEN_INSTALL_OPTION,
                     )


def get_environment_value(value_name):
    value = os.environ.get(value_name)
    if value is not None:
        return value
    else:
        raise EnvironmentError('Environment value "%s" must be set before generating this file.', value_name)


def get_settings_value(value_name):
    value = getattr(settings, value_name, None)
    if value is not None:
        return value
    else:
        raise ValueError('Settings value "%s" must be set before generating this file.', value_name)


def generate_command(args):
    """
    Generate a settings file for a new installation.
    """
    # Consts
    TETHYS_HOME = get_tethys_home_dir()
    TETHYS_SRC = get_tethys_src_dir()

    # Setup variables
    context = Context()

    # Determine template path

    gen_templates_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gen_templates')
    template_path = os.path.join(gen_templates_dir, args.type)

    # Parse template
    template = Template(open(template_path).read())

    # Determine destination file name (defaults to type)
    destination_file = FILE_NAMES[args.type]

    # Default destination path is the current working directory
    destination_dir = os.path.join(TETHYS_SRC, 'tethys_portal')

    nginx_user = ''
    nginx_conf_path = '/etc/nginx/nginx.conf'
    if os.path.exists(nginx_conf_path):
        with open(nginx_conf_path, 'r') as nginx_conf:
            for line in nginx_conf.readlines():
                tokens = line.split()
                if len(tokens) > 0 and tokens[0] == 'user':
                    nginx_user = tokens[1].strip(';')
                    break

    # Settings file setup
    if args.type == GEN_SETTINGS_OPTION:
        # Generate context variables
        secret_key = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(50)])
        installed_apps = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
                          'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
                          'django_gravatar','bootstrap3', 'termsandconditions', 'tethys_config', 'tethys_apps',
                          'tethys_gizmos', 'tethys_services', 'tethys_compute', 'tethys_quotas', 'social_django',
                          'guardian', 'session_security', 'captcha', 'rest_framework', 'rest_framework.authtoken',
                          'analytical', 'channels']

        if args.add_apps:
            if settings.INSTALLED_APPS:
                installed_apps = settings.INSTALLED_APPS

            for i in ast.literal_eval(args.add_apps):
                if str(i) not in installed_apps:
                    installed_apps.append(str(i))

        elif args.add_app and str(args.add_app) not in installed_apps:
            if settings.INSTALLED_APPS:
                installed_apps = settings.INSTALLED_APPS

            installed_apps.append(str(args.add_app))

        if args.remove_apps:
            if settings.INSTALLED_APPS:
                installed_apps = settings.INSTALLED_APPS

            for i in ast.literal_eval(args.remove_apps):
                if str(i) in installed_apps:
                    installed_apps.remove(str(i))
        elif args.remove_app and str(args.remove_app) in installed_apps:
            if settings.INSTALLED_APPS:
                installed_apps = settings.INSTALLED_APPS

            installed_apps.remove(str(args.remove_app))

        if args.session_expire_browser and args.session_expire_browser not in ['0', 'f', 'F', 'false', 'False']:
            session_expire_browser = True
        else:
            session_expire_browser = False

        try:
            session_warning = int(args.session_warning)
        except:
            session_warning = 840

        try:
            session_expire = int(args.session_expire)
        except:
            session_expire = 900

        if args.static_root and os.path.exists(args.static_root):
            static_root = args.static_root
        else:
            static_root = os.path.join(TETHYS_HOME, 'static')

        if args.workspaces_root and os.path.exists(args.workspaces_root):
            workspaces_root = args.workspaces_root
        else:
            workspaces_root = os.path.join(TETHYS_HOME, 'workspaces')

        if args.bypass_portal_home and args.bypass_portal_home not in ['0', 'f', 'F', 'false', 'False']:
            bypass_portal_home = True
        else:
            bypass_portal_home = False

        if args.open_signup and args.open_signup not in ['0', 'f', 'F', 'false', 'False']:
            open_signup = True
        else:
            open_signup = False

        if args.open_portal and args.open_portal not in ['0', 'f', 'F', 'false', 'False']:
            open_portal = True
        else:
            open_portal = False

        context.update({'secret_key': secret_key,
                        'allowed_host': args.allowed_host,
                        'allowed_hosts': args.allowed_hosts,
                        'db_username': args.db_username,
                        'db_password': args.db_password,
                        'db_port': args.db_port,
                        'db_host': args.db_host,
                        'tethys_home': TETHYS_HOME,
                        'production': args.production,
                        'open_portal': open_portal,
                        'installed_apps': installed_apps,
                        'session_expire_browser': session_expire_browser,
                        'session_warning': session_warning,
                        'session_expire': session_expire,
                        'static_root': static_root,
                        'workspaces_root': workspaces_root,
                        'bypass_portal_home': bypass_portal_home,
                        'open_signup': open_signup
                        })

    if args.type == GEN_NGINX_OPTION:
        hostname = str(settings.ALLOWED_HOSTS[0]) if len(settings.ALLOWED_HOSTS) > 0 else '127.0.0.1'
        workspaces_root = get_settings_value('TETHYS_WORKSPACES_ROOT')
        static_root = get_settings_value('STATIC_ROOT')

        context.update({'hostname': hostname,
                        'port': args.tethys_port,
                        'workspaces_root': workspaces_root,
                        'static_root': static_root,
                        'client_max_body_size': args.client_max_body_size
                        })

    if args.type == GEN_ASGI_SERVICE_OPTION:
        hostname = str(settings.ALLOWED_HOSTS[0]) if len(settings.ALLOWED_HOSTS) > 0 else '127.0.0.1'
        conda_home = get_environment_value('CONDA_HOME')
        conda_env_name = get_environment_value('CONDA_ENV_NAME')

        user_option_prefix = ''

        try:
            linux_distro = linux_distribution(full_distribution_name=0)[0]
            if linux_distro in ['redhat', 'centos']:
                user_option_prefix = 'http-'
        except Exception:
            pass

        context.update({'nginx_user': nginx_user,
                        'hostname': hostname,
                        'port': args.tethys_port,
                        'asgi_processes': args.asgi_processes,
                        'conda_home': conda_home,
                        'conda_env_name': conda_env_name,
                        'tethys_src': TETHYS_SRC,
                        'user_option_prefix': user_option_prefix
                        })

    if args.type in [GEN_SERVICES_OPTION, GEN_INSTALL_OPTION]:
        destination_dir = os.getcwd()

    if args.type == GEN_INSTALL_OPTION:
        print('Please review the generated install.yml file and fill in the appropriate information '
              '(app name is requited).')

    if args.directory:
        if os.path.isdir(args.directory):
            destination_dir = args.directory
        else:
            print('ERROR: "{0}" is not a valid directory.'.format(destination_dir))
            exit(1)

    destination_path = os.path.join(destination_dir, destination_file)

    # Check for pre-existing file
    if os.path.isfile(destination_path):
        valid_inputs = ('y', 'n', 'yes', 'no')
        no_inputs = ('n', 'no')

        if args.overwrite:
            overwrite_input = 'yes'
        else:
            overwrite_input = input('WARNING: "{0}" already exists. '
                                    'Overwrite? (y/n): '.format(destination_file)).lower()

            while overwrite_input not in valid_inputs:
                overwrite_input = input('Invalid option. Overwrite? (y/n): ').lower()

        if overwrite_input in no_inputs:
            print('Generation of "{0}" cancelled.'.format(destination_file))
            exit(0)

    # Render template and write to file
    if template:
        with open(destination_path, 'w') as f:
            f.write(template.render(context))
