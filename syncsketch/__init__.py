# -*- coding: utf-8 -*-
# @Author: yafes
# @Date:   2018-11-20 17:39:54
# @Last Modified by:   Brady Endres
# @Last Modified time: 2025-07-07

from __future__ import absolute_import

import sys
import warnings

if sys.version_info < (3, 8):
    warnings.warn(
        "SyncSketch: Python %d.%d is deprecated. "
        "New features will only target Python 3.8+. "
        "Please upgrade." % (sys.version_info[0], sys.version_info[1]),
        DeprecationWarning,
        stacklevel=2,
    )

from .syncsketch import SyncSketchAPI

__version__ = "1.0.12.0"
__author__ = "SyncSketch Dev Team"
__credits__ = "Philip Floetotto, Yafes Sahin, Brady Endres, Eric Palakovich Carr"
