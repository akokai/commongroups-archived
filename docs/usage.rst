Usage
=====

Environment
-----------

All files generated when you use camelid are stored within a "home" environment. Within this, you can maintain multiple different "project" environments, in which you use camelid to work on separate collections of data, results, logs, etc.

-  The root *camelid home* directory contains all of the project directories.
   You can specify where this is in a number of ways:

   -  Set an an environment variable ``CAMELID_HOME``::

      $ export CAMELID_HOME=/path/to/camelid_home

   -  When running the camelid script, use the option
      ``-e /path/to/camelid_home``.
   -  If you don't specify anything: it defaults to
      ``<user home>/camelid_data``.

-  *Projects* can have any name you want, and will reside in a corresponding
   subdirectory within the camelid home. You can have any number of projects.
   
   -  Project directories contain ``data``, ``log``, and ``results``
      subdirectories.
   -  If you don't specify a project, your data will go in
      ``<camelid home>/default``. 
   -  If you run the unit tests for :mod:`camelid`, some of them will create a
      project called ``test``.

All of these directories are created automatically.

Notes
^^^^^

When loading chemical group parameters from a JSON file, the expected file location is ``<project path>/params.json``.


.. _googlesetup:

Google Sheets access
--------------------

To access the Google Sheet that contains CMG parameters, you must have Google service account credentials, and you must specify the path to a JSON file containing those credentials.

Setup
^^^^^

-  See the `gspread docs`_ for instructions on getting OAuth2 credentials for
   Google Drive API access.
-  Download a JSON file containing your Google service account credentials and
   save it somewhere secure.
-  There are three ways to use your credentials:

   -  Set the environment variable ``CAMELID_KEYFILE``::

      $ export CAMELID_KEYFILE=/path/to/credentials.json

      That way you never have to think about it again.
   -  When running the camelid script, use the option
      ``-k /path/to/credentials.json``.
   -  Pass they argument ``key_file=/path/to/credentials.json`` when creating
      either a :class:`camelid.run.CamelidEnv` or a
      :class:`camelid.googlesheet.SheetManager`.

-  Don't forget to share the relevant Google Sheet with your Google
   service account client e-mail address (it's in the key file).

.. _gspread docs: https://gspread.readthedocs.io/


.. _running:

Running camelid
---------------

The script can be run from the repository root directory using::

   python -m camelid.run [options]


Options
^^^^^^^

Use the option ``--help`` to get a list of all the options. Here is a partial list of available options that may not reflect recent changes.

``-r``, ``--resume_update``
   Resume the previous update (e.g., if it failed).

``-c``, ``--clean_start``
   Do not resume previous searches, and delete existing data before starting.

``-p PROJECT``, ``--project PROJECT``
   Project name.

``-e ENV_PATH``, ``--env_path ENV_PATH``
   Path to camelid home.

``-w WORKSHEET``, ``--worksheet WORKSHEET``
   Worksheet to get parameters from.

``-k KEY_FILE``, ``--key_file KEY_FILE``
   Path to Google API key file.

``-j JSON_FILE``, ``--json_file  JSON_FILE``
   Read parameters from a JSON file.
