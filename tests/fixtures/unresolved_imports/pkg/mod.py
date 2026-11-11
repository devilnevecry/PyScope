"""pkg.mod imports stdlib, third-party, and unresolved modules."""

import os
import json
import nonexistent_module_xyz
from collections import OrderedDict
from some_missing_package import something

VALUE = 1

from .ghost import specter  # dangling relative import
