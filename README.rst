camelid
=======

|A group of camelids|

Project for meta-organizing chemical and material libraries.

.. |A group of camelids| image:: https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Alpacas.JPG/640px-Alpacas.JPG


.. All data, logs, etc. are stored in an "off-site" environment, and you can use camelid with multiple different "projects". This should massively reduce my confusion in moving around files with names like `2072101`.

.. - There is a camelid home directory that you can specify in a number of ways such as an environment variable `CAMELID_HOME`. Defaults to `<user home>/camelid_data`.
.. - Within the camelid home directory,  you can have many subdirectories for different "projects". You can name them what you want, and if you don't choose a name you get a project in `<camelid home>/default`. Project directories contain `data`, `log`, and `results` directories.
.. - If loading CMG parameters from a JSON file, the expected file is `<project>/params.json`.

.. There's also a new object-oriented mechanism for managing access to Google Sheets. You need to specify the path to your API credentials JSON file, or set the environment variable `CAMELID_KEYFILE`.

.. The script can be run from the repository root directory using `python -m camelid.run [options | --help]`