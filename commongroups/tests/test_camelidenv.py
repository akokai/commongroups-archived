# -*- coding: utf-8 -*-
"""Unit tests for commongroups run environment."""

import os

from commongroups.env import CommonEnv


def test_commongroupsenv():
    env = CommonEnv(project='test')
    assert os.path.exists(env.log_file)
    env.clear_logs()
    assert not os.path.exists(env.log_file)
