# coding: utf-8

"""Environment for compound group operations."""

from datetime import datetime
from itertools import islice
import json
import logging
import os
from os.path import join as pjoin

from boltons.fileutils import mkdir_p

from commongroups import logconf  # pylint: disable=unused-import
from commongroups import cmgroup as cmg
from commongroups import googlesheet as gs

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def add_project_handler(log_file):
    """
    Add a project-specific :class:`FileHandler` for all logging output.

    This enables logging to a file that's kept within the project
    directory.
    """
    loggers = list(logconf.CONFIG['loggers'].keys())
    proj_handler = logging.FileHandler(log_file, mode='w')
    fmt = logging.getLogger('commongroups').handlers[0].formatter
    proj_handler.setFormatter(fmt)
    for item in loggers:
        lgr = logging.getLogger(item)
        lgr.addHandler(proj_handler)


class CommonEnv(object):
    """
    Run environment for :mod:`commongroups`.

    This object keeps track of a project environment (i.e., file locations
    for data and logs, common parameters) for many instances of
    :class:`commongroups.cmgroup.CMGroup`.

    Instantiating this class creates a directory structure and a log file.
    Namely, a project directory corresponding to ``project_path`` and its
    subdirectories ``results_path``, ``log_path``, ``data_path``. The
    project directory is created within the "home" directory corresponding
    to ``env_path``. A new log file is created each time a new ``CommonEnv``
    with the same project name is created.

    Parameters:
        name (str): Project name, used to name the project directory.
        env_path (str): Path to root commongroups home. If not specified,
            looks for environment variable ``CMG_HOME`` or defaults to
            ``~/commongroups_data``.
    """
    def __init__(self,
                 name='default',
                 env_path=None):
        if env_path:
            self._env_path = os.path.abspath(env_path)
        elif os.getenv('CMG_HOME'):
            self._env_path = os.path.abspath(os.getenv('CMG_HOME'))
        else:
            self._env_path = pjoin(os.path.expanduser('~'),
                                   'commongroups_data')

        self._name = name
        self._project_path = pjoin(self._env_path, name)
        mkdir_p(self._project_path)

        # Set up per-project logging to file.
        self._log_path = pjoin(self._project_path, 'log')
        log_path = pjoin(self._project_path, 'log')
        mkdir_p(log_path)
        log_file = pjoin(log_path,
                         datetime.now().strftime('%Y%m%dT%H%M%S') + '.log')
        add_project_handler(log_file)

        # Set up data and results directories.
        self._data_path = pjoin(self._project_path, 'data')
        mkdir_p(self._data_path)
        self._results_path = pjoin(self._project_path, 'results')
        mkdir_p(self._results_path)

        # Log where the directories & files have been created.
        logger.info('Project path: %s', self._project_path)

        # Configuation parameters do not exist until loaded.
        self.config = None

    # The following attributes are read-only because changing them would
    # result in inconsitencies with file paths.
    @property
    def name(self):
        """Project name."""
        return self._name

    @property
    def project_path(self):
        """Path to project directory."""
        return self._project_path

    # @property
    # def log_path(self):
    #     """Path to project log directory."""
    #     return self._log_path

    # @property
    # def log_file(self):
    #     """Path to the currently active log file."""
    #     return self._log_file

    @property
    def data_path(self):
        """Path to the project data directory."""
        return self._data_path

    @property
    def results_path(self):
        """Path to the project results directory."""
        return self._results_path

    def __repr__(self):
        args = [self._name, self._env_path]
        return 'CommonEnv({})'.format(', '.join(args))

    def __str__(self):
        return 'CommonEnv({})'.format(self._name)

    def _get_config_path(self, config_path=None):
        if config_path:
            in_proj = pjoin(self._env_path, config_path)
            if os.path.exists(in_proj):
                config_path = in_proj
            else:
                config_path = os.path.abspath(config_path)
        else:
            config_path = pjoin(self._env_path, 'config.json')
        return config_path

    def read_config(self, config_path=None):
        """
        Load and return user-configured operating parameters as a dict.

        Parameters:
            config_path: Optional; path to an alternative JSON file.
        """
        config_path = self._get_config_path(config_path)
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        logger.debug('Read config file: %s', config_path)
        return config

    def write_config(self, config_data, config_path=None):
        """
        Rewrite the user-configured operating parameters file.

        Parameters:
            config_data (dict): New parameters to replace existing ones.
            config_path: Optional; path to an alternative JSON file.
        """
        config_path = self._get_config_path(config_path)
        with open(config_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=2, sort_keys=True)

    def get_config(self):
        if not self.config:
            self.config = self.read_config()
        return self.config

    def run(self, args):  # TODO: Update!
        """
        Perform operations specified by the arguments.

        See :ref:`Running commongroups <running>` for possible operations.

        Parameters:
            args (dict): Parsed command-line arguments.

        Notes:
            The "resume update" option is handled by
            :func:`commongroups.cmgroup.batch_cmg_search`.
        """
        if args.json_file:
            logger.info('Generating compound groups from JSON file')
            cmg_gen = cmg.cmgs_from_json(args.json_file, self)
        else:
            logger.info('Generating compound groups from Google Sheet')
            sheet = gs.SheetManager(args.sheet_name, args.worksheet)
            cmg_gen = sheet.get_cmgs(self)

        groups = list(islice(cmg_gen, None))

        # if args.clean_start:
        #     logger.debug('Clearing data and logs')
        #     for group in groups:
        #         group.clear_data()
        #     self.clear_logs()

        logger.info('Starting batch CMG update process')
        try:
            cmg.batch_cmg_search(groups)
        except:
            logger.exception('Process failed')
            import pdb; pdb.set_trace()
