# -*- coding: utf-8 -*-
"""Unit tests for camelid run environment."""

import os

from ..run import CamelidEnv


def test_camelidenv():
    env = CamelidEnv(project='test')
    assert os.path.exists(env.log_file)
    env.clear_logs()
    assert not os.path.exists(env.log_file)
