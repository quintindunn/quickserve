"""
List of all PeeWee models, used for database instantiation.
"""

from QuickServeDatabase.network import OccupiedPortModel
from QuickServeDatabase.instances import InstanceModel

MODELS = [OccupiedPortModel, InstanceModel]
