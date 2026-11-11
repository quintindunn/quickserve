import argparse
import getpass

from werkzeug.security import generate_password_hash

from QuickServe.Database.database import create_database
from QuickServe.Database.models import MODELS
from QuickServe.Database.users import UserModel
from QuickServe.FileSystem.config import Config
from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.Database.database import connect as db_connect
from QuickServe.Database.database import initialize as db_initialize

workspace = Workspace()

config = Config(workspace=workspace)

database = create_database(file_path=config.database.file_path)
db_initialize(database=database)
db_connect(database=database)
database.create_tables(models=MODELS)


def create_admin(username: str | None = None):
    if not username:
        username = input("Username: ").strip()

    if len(username) <= 4 or len(username) >= 20:
        print("Error: Username must be between 4 and 20 characters.")
        return

    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Password (again): ")

    if password != password_confirm:
        print("Error: Passwords do not match. Please try again.")
        return

    if not password:
        print("Error: Password cannot be empty.")
        return


    if len(password) < 8 or len(password) > 32:
        print("Error: Password must be between 5 and 32 characters.")

    print(f"Creating admin: {username}")

    UserModel.create(
        username=username,
        password_hash=generate_password_hash(password),
    )

def delete_user(username: str | None = None):
    if not username:
        username = input("Username: ").strip()

    try:
        user = UserModel.get(UserModel.username == username)
    except UserModel.DoesNotExist:
        print(f"Error: No user found with username {username!r}.")
        return


    confirmed = input(f"Delete user {username}? THIS CANNOT BE UNDONE! (y/n)")
    if confirmed.lower() == "n":
        print("Canceling.")
        return
    elif confirmed.lower() != "y":
        print(f"Error: invalid input {confirmed!r}.")
        return

    UserModel.delete_by_id(user.id)
    print(f"User {username} deleted.")



parser = argparse.ArgumentParser(prog="quickserve")
subparsers = parser.add_subparsers(dest="command", required=True)

admin_parser = subparsers.add_parser(
    "createadmin",
    help="Create an admin account."
)
admin_parser.add_argument("--username", help="Username")

delete_parser = subparsers.add_parser(
    "deleteuser",
    help="Delete a user account"
)
delete_parser.add_argument("--username", help="USername")

args = parser.parse_args()

if args.command == "createadmin":
    create_admin(args.username)
elif args.command == "deleteuser":
    delete_user(args.username)