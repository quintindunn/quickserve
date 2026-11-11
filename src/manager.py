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


def get_password() -> str | None:
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Password (again): ")

    if password != password_confirm:
        print("Error: Passwords do not match. Please try again.")
        return None

    if not password:
        print("Error: Password cannot be empty.")
        return None

    if len(password) < 8 or len(password) > 32:
        print("Error: Password must be between 8 and 32 characters.")
        return None

    return password


def create_admin(username: str | None = None):
    if not username:
        username = input("Username: ").strip()

    if len(username) <= 4 or len(username) >= 20:
        print("Error: Username must be between 5 and 19 characters.")
        return

    password = get_password()

    if password is None:
        return

    print(f"Creating admin: {username}")

    UserModel.create(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=True
    )

    print(f"Admin {username} created successfully.")


def delete_user(username: str | None = None):
    if not username:
        username = input("Username: ").strip()

    try:
        user = UserModel.get(UserModel.username == username)
    except UserModel.DoesNotExist:
        print(f"Error: No user found with username {username!r}.")
        return

    confirmed = (
        input(f"Delete user {username}? THIS CANNOT BE UNDONE! (y/n): ").strip().lower()
    )

    if confirmed == "n":
        print("Canceling.")
        return
    elif confirmed != "y":
        print(f"Error: Invalid input {confirmed!r}.")
        return

    user.delete_instance()
    print(f"User {username} deleted.")


def change_password(username: str | None = None):
    if not username:
        username = input("Username: ").strip()

    try:
        user = UserModel.get(UserModel.username == username)
    except UserModel.DoesNotExist:
        print(f"Error: No user found with username {username!r}.")
        return

    password = get_password()

    if password is None:
        return

    user.password_hash = generate_password_hash(password)
    user.save()

    print(f"Password changed for user {username}.")


def list_users():
    users = UserModel.select()

    if not users.exists():
        print("No users found.")
        return

    print(f"{'ID':<6} {'Username':<20}")
    print("-" * 26)

    for user in users:
        print(f"{user.id:<6} {user.username:<20}")

    print(f"\nTotal users: {users.count()}")


parser = argparse.ArgumentParser(prog="quickserve")
subparsers = parser.add_subparsers(dest="command", required=True)

admin_parser = subparsers.add_parser("createadmin", help="Create an admin account.")
admin_parser.add_argument("--username", help="Username")

delete_parser = subparsers.add_parser("deleteuser", help="Delete a user account.")
delete_parser.add_argument("--username", help="Username")

password_parser = subparsers.add_parser(
    "changepassword", help="Change a user's password."
)
password_parser.add_argument("--username", help="Username")

subparsers.add_parser(
    "listusers",
    help="List all user accounts."
)

args = parser.parse_args()

if args.command == "createadmin":
    create_admin(args.username)

elif args.command == "deleteuser":
    delete_user(args.username)

elif args.command == "changepassword":
    change_password(args.username)

elif args.command == "listusers":
    list_users()
