"""
List of all PeeWee models, used for database instantiation.

Author: Quintin Dunn
Date: 09/14/2026
"""

from QuickServe.Database.network import OccupiedPortModel
from QuickServe.Database.instances import InstanceModel

MODELS = [OccupiedPortModel, InstanceModel]
