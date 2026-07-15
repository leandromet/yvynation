"""Coverage report: python -m yvynation.utils.translations"""

import sys

from . import coverage_report

sys.exit(0 if coverage_report() else 1)
