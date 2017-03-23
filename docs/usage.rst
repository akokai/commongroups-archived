Usage
=====

Environment
-----------

All files generated when you use commongroups are stored within a "home" environment. Within this, you can maintain multiple different "project" environments, in which you use commongroups to work on separate collections of data, results, logs, etc.

-  The root *commongroups home* directory contains all of the project directories.
   You can specify where this is in a number of ways:

   -  Set an an environment variable ``CMGROUPS_HOME``::

      $ export CMGROUPS_HOME=/path/to/commongroups_home

   -  When running the commongroups script, use the option
      ``-e /path/to/commongroups_home``.
   -  If you don't specify anything: it defaults to
      ``<user home>/commongroups_data``.

-  *Projects* can have any name you want, and will reside in a corresponding
   subdirectory within the commongroups home. You can have any number of projects.

   -  Project directories contain ``data``, ``log``, and ``results``
      subdirectories.
   -  If you don't specify a project, your data will go in
      ``<commongroups home>/default``.
   -  If you run the unit tests for :mod:`commongroups`, some of them will create a
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
-  To use your credentials: **TBD**
-  Don't forget to share the relevant Google Sheet with your Google
   service account client e-mail address (it's in the key file).

.. _gspread docs: https://gspread.readthedocs.io/

.. _running:

Running commongroups
---------------

**This information is subject to change.** The script can be run from the repository root directory using::

   python -m commongroups.run [options]

Options
^^^^^^^

Use the option ``--help`` to get a list of all the options.
