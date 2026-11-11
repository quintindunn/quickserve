"""
List of all PeeWee models, used for database instantiation.

Author: Quintin Dunn
Date: 09/14/2026
"""

from QuickServe.Database.instances import InstanceModel
from QuickServe.Database.users import UserModel

MODELS = [InstanceModel, UserModel]
