"""
List of all PeeWee models, used for database instantiation.
"""

from QuickServe.Database.network import OccupiedPortModel
from QuickServe.Database.instances import InstanceModel

MODELS = [OccupiedPortModel, InstanceModel]
