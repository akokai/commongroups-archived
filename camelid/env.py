# coding: utf-8

"""Environment for compound group operations."""

from datetime import datetime
from itertools import islice
import json
import logging
import os
from os.path import join as pjoin

from boltons.fileutils import mkdir_p

from camelid import logconf  # pylint: disable=unused-import
from camelid import cmgroup as cmg
from camelid import googlesheet as gs

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class CamelidEnv(object):
    """
    Run environment for :mod:`camelid`. Prefers desert or alpine habitats.

    This object keeps track of a project environment (i.e., file locations
    for data and logs, common parameters) for many instances of
    :class:`camelid.cmgroup.CMGroup`.

    Instantiating this class creates a directory structure and a log file.
    Namely, a project directory corresponding to ``project_path`` and its
    subdirectories ``results_path``, ``log_path``, ``data_path``. The
    project directory is created within the "home" directory corresponding
    to ``env_path``. A new log file is created each time a new ``CamelidEnv``
    with the same project name is created.

    Parameters:
        name (str): Project name, used to name the project directory.
        database (str): Database URL for connecting to structure-searchable
            database.
        env_path (str): Path to root camelid home. If not specified,
            looks for environment variable ``CAMELID_HOME`` or defaults to
            ``~/camelid_data``.
    """
    def __init__(self,
                 name='default',
                 env_path=None):
        if env_path:
            self._env_path = os.path.abspath(env_path)
        elif os.getenv('CAMELID_HOME'):
            self._env_path = os.path.abspath(os.getenv('CAMELID_HOME'))
        else:
            self._env_path = pjoin(os.path.expanduser('~'), 'camelid_data')

        self._name = name
        self._project_path = pjoin(self._env_path, name)
        mkdir_p(self._project_path)

        # Set up per-project logging to file.
        self._log_path = pjoin(self._project_path, 'log')
        mkdir_p(self._log_path)
        log_file = datetime.now().strftime('%Y%m%dT%H%M%S') + '.log'
        self._log_file = pjoin(self._log_path, log_file)
        self.add_project_handler()
        logger.info('Project path: %s', self._project_path)

        # Set up data and results directories.
        self._data_path = pjoin(self._project_path, 'data')
        mkdir_p(self._data_path)
        self._results_path = pjoin(self._project_path, 'results')
        mkdir_p(self._results_path)

    @property
    def name(self):
        """Project name."""
        return self._name

    @property
    def project_path(self):
        """Path to project directory."""
        return self._project_path

    @property
    def log_path(self):
        """Path to project log directory."""
        return self._log_path

    @property
    def log_file(self):
        """Path to the currently active log file."""
        return self._log_file

    @property
    def data_path(self):
        """Path to the project data directory."""
        return self._data_path

    @property
    def results_path(self):
        """Path to the project results directory."""
        return self._results_path

    def __repr__(self):
        args = [self._name, self._database, self._env_path]
        return 'CamelidEnv({})'.format(', '.join(args))

    def __str__(self):
        return 'CamelidEnv({})'.format(self._name)

    def add_project_handler(self):
        """
        Add a project-specific :class:`FileHandler` for all logging output.

        This enables logging to a file that's kept within the project
        directory.
        """
        loggers = list(logconf.CONFIG['loggers'].keys())
        proj_handler = logging.FileHandler(self._log_file, mode='w')
        fmt = logging.getLogger('camelid').handlers[0].formatter
        proj_handler.setFormatter(fmt)
        for item in loggers:
            lgr = logging.getLogger(item)
            lgr.addHandler(proj_handler)

    def read_config(self, config_path=None):
        """
        Load, and return, user-configured operating parameters.

        Parameters:
            config_path: Optional; path to an alternative JSON file.
        """
        if config_path:
            in_proj = pjoin(self._env_path, config_path)
            if os.path.exists(in_proj):
                config_path = in_proj
            else:
                config_path = os.path.abspath(config_path)
        else:
            config_path = pjoin(self._env_path, 'config.json')
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config

    def run(self, args):  # TODO: Update!
        """
        Perform operations specified by the arguments.

        See :ref:`Running camelid <running>` for possible operations.

        Parameters:
            args (dict): Parsed command-line arguments.

        Notes:
            The "resume update" option is handled by
            :func:`camelid.cmgroup.batch_cmg_search`.
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
