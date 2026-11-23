import datetime
import hashlib
import hmac
import os
from pathlib import Path
from typing import Callable
from markupsafe import Markup

from QuickServe.Common.file_size_conversion import convert_size
from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request
from QuickServe.Common.file_signatures import SIGNATURES

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.Web import Registry

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

    return Markup(f"""
        <script>
            window.location = `{url}`;
        </script>
    """)


def sort_name(file_path: Path):
    return file_path.name.lower()


def sort_size(file_path: Path):
    return file_path.stat().st_size


def sort_type(file_path: Path):
    return file_path.is_dir()


def sort_extension(file_path: Path):
    return file_path.suffix.lower()


def sort_date_created(file_path: Path):
    return file_path.stat().st_ctime


def sort_date_modified(file_path: Path):
    return file_path.stat().st_mtime


def sort_date_accessed(file_path: Path):
    return file_path.stat().st_atime


def sort_directories_first(file_path: Path):
    return not file_path.is_dir()


def sort_files_first(file_path: Path):
    return file_path.is_dir()


sorting_methods = {
    "name_ascending": (sort_name, False),
    "name_descending": (sort_name, True),
    "size_ascending": (sort_size, False),
    "size_descending": (sort_size, True),
    "type_ascending": (sort_type, False),
    "type_descending": (sort_type, True),
    "extension_ascending": (sort_extension, False),
    "extension_descending": (sort_extension, True),
    "date_created_ascending": (sort_date_created, False),
    "date_created_descending": (sort_date_created, True),
    "date_modified_ascending": (sort_date_modified, False),
    "date_modified_descending": (sort_date_modified, True),
    "date_accessed_ascending": (sort_date_accessed, False),
    "date_accessed_descending": (sort_date_accessed, True),
    "directories_first": (sort_directories_first, False),
    "files_first": (sort_files_first, False),
}


def simple_filesystem_builder(
    registry: "Registry", module_name: str
) -> Callable[[], str]:
    resource_folder: str = str(
        get_resource("simple_filesystem_folder_viewer.html", mode="r")
    )
    resource_file: str = str(
        get_resource("simple_filesystem_file_viewer.html", mode="r")
    )

    def format_date(dt: datetime.datetime):
        return dt.strftime("%m/%d/%Y %I:%M:%S%p")

    def render_folder(
        root: str,
        instance: "BaseInstance",
        hashed_root: str,
        sort_function: Callable[[Path], bool | int | str],
        reverse_sorting: bool,
    ):
        directory = request.args.get("directory") or ""
        working_dir = instance.working_directory() / root.lstrip("/") / directory

        is_valid = is_child(
            instance.working_directory() / root.lstrip("/"), working_dir
        )

        if is_valid:
            listed_folders = []
            listed_files = []

            for file in os.listdir(working_dir):
                file_path = working_dir / file

                if os.path.isfile(file_path):
                    listed_files.append(file_path)
                else:
                    listed_folders.append(file_path)

            listed_folders.extend(listed_files)

            listed_folders.sort(key=sort_function, reverse=reverse_sorting)
        else:
            listed_folders = []

        files = []
        for file_path in listed_folders:
            file = file_path.name

            files.append(
                {
                    "filename": file,
                    "cwd": directory.lstrip(".") + "/",
                    "modified": format_date(
                        datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    ),
                    "size": convert_size(os.stat(file_path).st_size, precision=1),
                    "isFile": os.path.isfile(file_path),
                    "isDir": os.path.isdir(file_path),
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
            "parent_folder": Path(directory).parent,
            "root_directory": root_dir if root_dir != "./." else "./",
            "instance": instance,
            "hashed_root": hashed_root,
        }

        template = current_app.jinja_env.from_string(resource_folder)
        return Markup(template.render(context=context))

    def render_file(root: str, instance: "BaseInstance", hashed_root: str):
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
            "hashed_root": hashed_root,
            "filepath": request.args["file"],
            "parent": ("./" + str(Path(request.args["file"]).parent)),
        }
        template = current_app.jinja_env.from_string(resource_file)
        return Markup(template.render(context=context))

    def simple_filesystem(root: str = "/", sort_by: str = "name_ascending"):
        """
        Creates an easy-to-use file system.
        :param root: The root directory of the filesystem
        :param sort_by: Sorting method.

        Available sorting methods:
        - name_ascending
        - name_descending
        - size_ascending
        - size_descending
        - type_ascending
        - type_descending
        - extension_ascending
        - extension_descending
        - date_created_ascending
        - date_created_descending
        - date_modified_ascending
        - date_modified_descending
        - date_accessed_ascending
        - date_accessed_descending
        - directories_first
        - files_first
        :return:
        """

        hashed_root = hmac.new(
            registry.registered_controller_roots_salt, root.encode(), hashlib.sha256
        ).hexdigest()

        registry.registered_controller_roots[hashed_root] = root

        assert hasattr(request, "instance")

        if sort_by not in sorting_methods:
            raise ValueError("Invalid sorting method")

        instance: "BaseInstance" = getattr(request, "instance")

        file = request.args.get("file")

        sort_fn, reverse_sort = sorting_methods[sort_by]
        if file is None:
            return render_folder(
                root=root,
                instance=instance,
                hashed_root=hashed_root,
                sort_function=sort_fn,
                reverse_sorting=reverse_sort,
            )
        else:
            return render_file(root=root, instance=instance, hashed_root=hashed_root)

    return simple_filesystem
