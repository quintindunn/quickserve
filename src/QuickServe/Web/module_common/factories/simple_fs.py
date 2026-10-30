import datetime
import os
from pathlib import Path
from typing import Callable
from markupsafe import Markup

from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request
from QuickServe.Common.file_signatures import SIGNATURES

max_signature_length = max([len(s) // 2 for s in SIGNATURES])
max_file_size = 102400


def is_child(instance_root: Path, requested_path: Path) -> bool:
    """
    Checks if the requested path should be visible to the client.
    :param instance_root: The root of the instance that is being requested's working dir.
    :param requested_path: The requested path.
    :return: True if they should have access, otherwise False.
    """
    requested_path = requested_path.resolve()
    return requested_path.is_relative_to(instance_root.resolve())


def is_file_editable(requested_path: Path) -> bool:
    """
    Checks if the requested path's file should be editable.
    :param requested_path: The requested path.
    :return: True if the file should be editable, otherwise False.
    """

    path = requested_path.resolve()

    if not path.is_file():
        return False

    file_size = path.stat().st_size
    if file_size > max_file_size:
        return False

    with path.open("rb") as f:
        magic_number = f.read(max_signature_length)

    for signature in SIGNATURES:
        if signature_matches(signature, magic_number):
            return False

    with path.open("rb") as f:
        first_4kb = f.read(4096)

        try:
            first_4kb.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False


def signature_matches(signature: str, heading: bytes) -> bool:
    """
    Checks whether a file signature matches the beginning of a file.

    Signatures are hexadecimal strings, optionally containing ?? wildcards
    that match any single byte.

    Examples:
        4E555255494D474E55525550414C
        FFD8FFE1????457869660000

    Signatures can be shorter than heading.
    :param signature: The hexadecimal file signature to match.
    :param heading: The beginning of the file.
    :return: Whether the signature matches the heading.
    """
    if len(signature) % 2 != 0:
        return False

    signature_bytes = bytes.fromhex(signature.replace("??", "00"))
    wildcard_bytes = {
        i // 2 for i in range(0, len(signature), 2) if signature[i : i + 2] == "??"
    }

    if len(signature_bytes) > len(heading):
        return False

    return all(
        i in wildcard_bytes or signature_bytes[i] == heading[i]
        for i in range(len(signature_bytes))
    )


def _redirect(url: str) -> Markup:
    """
    ** UNSAFE **
    Generated an HTML script tag containing a redirect to a URL.
    :param url: The URL to redirect to.
    :return: Markup object containing the script tag.
    """

    return Markup(
        f"""
        <script>
            window.location = `{url}`;
        </script>
    """
    )


def simple_filesystem_builder(module_name: str) -> Callable[[], str]:
    resource_folder: str = str(
        get_resource("simple_filesystem_folder_viewer.html", mode="r")
    )
    resource_file: str = str(
        get_resource("simple_filesystem_file_viewer.html", mode="r")
    )

    def format_date(dt: datetime.datetime):
        return dt.strftime("%m/%d/%Y %I:%M:%S%p")

    def render_folder(root: str, instance: "BaseInstance"):
        directory = request.args.get("directory") or ""
        working_dir = instance.working_directory() / root.lstrip("/") / directory

        is_valid = is_child(
            instance.working_directory() / root.lstrip("/"), working_dir
        )

        if is_valid:
            listed_folders = []
            listed_files = []

            for file in os.listdir(working_dir):
                if os.path.isfile(working_dir / file):
                    listed_files.append(file)
                else:
                    listed_folders.append(file)

            listed_folders.extend(listed_files)
        else:
            listed_folders = []

        files = []
        for file in listed_folders:
            file_path = working_dir / file
            files.append(
                {
                    "filename": file,
                    "cwd": directory.lstrip(".") + "/",
                    "modified": format_date(
                        datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    ),
                    "size": f"{os.stat(file_path).st_size / 1000:.1f}kb",
                    "isFile": os.path.isfile(file_path),
                    "isDir": os.path.isdir(file_path),
                    "isEmptyDir": os.path.isdir(file_path)
                    and not any(os.scandir(file_path)),
                    "canEdit": (
                        False
                        if os.path.isdir(file_path)
                        else is_file_editable(file_path)
                    ),
                }
            )

        root_dir = f"./{Path(directory)}"
        context = {
            "module_name": module_name,
            "files": files,
            "parent_folder": (Path(directory)).parent,
            "root_directory": root_dir if root_dir != "./." else "./",
            "instance": instance,
        }
        template = current_app.jinja_env.from_string(resource_folder)
        return Markup(template.render(context=context))

    def render_file(root: str, instance: "BaseInstance"):
        file = instance.working_directory() / root.lstrip("/") / request.args["file"]

        if not is_child(
            instance_root=instance.working_directory() / root.lstrip("/"),
            requested_path=file,
        ):
            return _redirect("/")

        try:
            with open(file, "r") as f:
                file_contents = f.read()
        except UnicodeDecodeError:
            raise NotImplementedError("Downloading files not implemented!")

        context = {
            "filename": file.name,
            "content": file_contents,
            "readOnly": request.args.get("edit") is None,
            "instance": instance,
            "filepath": request.args["file"],
            "parent": ("./" + str(Path(request.args["file"]).parent)),
        }
        template = current_app.jinja_env.from_string(resource_file)
        return Markup(template.render(context=context))

    def simple_filesystem(root: str = "/"):
        assert hasattr(request, "instance")

        instance: "BaseInstance" = getattr(request, "instance")

        file = request.args.get("file")

        if file is None:
            return render_folder(root=root, instance=instance)
        else:
            return render_file(root=root, instance=instance)

    return simple_filesystem
