"""
Downloader class for Minecraft servers

Author: Quintin Dunn
Date: 09/09/2026
"""

from enum import Enum
from functools import lru_cache

import requests
from pydantic import BaseModel
from datetime import datetime

import logging

logger = logging.getLogger("minecraft.downloader")


class VersionManifestLatestRelease(BaseModel):
    release: str
    snapshot: str


class VersionManifestReleaseTypeEnum(str, Enum):
    release = "release"
    snapshot = "snapshot"
    old_beta = "old_beta"
    old_alpha = "old_alpha"


class VersionManifestRelease(BaseModel):
    id: str
    type: VersionManifestReleaseTypeEnum
    release_url: str
    time: datetime
    release_time: datetime
    sha1: str
    compliance_level: int


class VersionManifest(BaseModel):
    latest: VersionManifestLatestRelease
    versions: dict[str, VersionManifestRelease]


class JavaComponentEnum(str, Enum):
    jre_legacy = "jre-legacy"
    java_runtime_alpha = "java-runtime-alpha"
    java_runtime_beta = "java-runtime-beta"
    java_runtime_gamma = "java-runtime-gamma"
    java_runtime_delta = "java-runtime-delta"
    java_runtime_epsilon = "java-runtime-epsilon"


class Java(BaseModel):
    component: JavaComponentEnum
    major_version: int


class ReleaseManifestServer(BaseModel):
    sha1: str
    size: int
    url: str


class ReleaseManifest(BaseModel):
    java: Java
    server: ReleaseManifestServer

# Requests made to OmniArchive servers should include the GitHub repo, project name, and contact info in the User-Agent.
OMNI_ARCHIVE_BASE = "https://vault.omniarchive.uk/archive/java/"
OMNI_ARCHIVE_MAP: dict[str, str] = {
    "1.2.4": "server-release/1.2/1.2.4.jar",
    "1.2.3": "server-release/1.2/1.2.3.jar",
    "1.2.2": "server-release/1.2/1.2.2.jar",
    "1.2.1": "server-release/1.2/1.2.1.jar",
    "1.1": "server-release/1.1/1.1.jar",
    "1.0": "server-beta/b1.9/pre/b1.9-pre6.jar",

    "b1.8.1": "server-beta/b1.8/b1.8.1.jar",
    "b1.8": "server-beta/b1.8/b1.8.jar",
    "b1.7.3": "server-beta/b1.7/b1.7.3.jar",
    "b1.7.2": "server-beta/b1.7/b1.7.2.jar",
    "b1.7": "server-beta/b1.7/b1.7.jar",
    "b1.6.6": "server-beta/b1.6/b1.6.6.jar",
    "b1.6.5": "server-beta/b1.6/b1.6.5.jar",
    "b1.6.4": "server-beta/b1.6/b1.6.4.jar",
    "b1.6.3": "server-beta/b1.6/b1.6.3.jar",
    "b1.6.2": "server-beta/b1.6/b1.6.2.jar",
    "b1.6.1": "server-beta/b1.6/b1.6.1.jar",
    "b1.6": "server-beta/b1.6/b1.6.jar",
    "b1.5_01": "server-beta/b1.5/b1.5_01.jar",
    "b1.5": "server-beta/b1.5/b1.5.jar",
    "b1.4_01": "server-beta/b1.4/b1.4_01.jar",
    "b1.4": "server-beta/b1.4/b1.4.jar",
    "b1.3_01": "server-beta/b1.3/b1.3-1731.jar",
    "b1.3b": "server-beta/b1.3/b1.3-1731.jar",
    "b1.2_02": "server-beta/b1.2/b1.2_01.jar",
    "b1.2_01": "server-beta/b1.2/b1.2_01.jar",
    "b1.2": "server-beta/b1.2/b1.2.jar",
    "b1.1_02": "server-beta/b1.1/b1.1_02.jar",
    "b1.1_01": "server-beta/b1.1/b1.1_01.jar",
    "b1.0.2": "server-beta/b1.0/b1.0_01.jar",
    "b1.0_01": "server-beta/b1.0/b1.0_01.jar",
    "b1.0": "server-beta/b1.0/b1.0.jar",

    "a1.2.6": "server-alpha/a0.2.8.jar",
    "a1.2.5": "server-alpha/a0.2.7.jar",
    "a1.2.4_01": "server-alpha/a0.2.6_02.jar",
    "a1.2.3_04": "TODO: FIND",
    "a1.2.3_02": "server-alpha/a0.2.5_02.jar",
    "a1.2.3_01": "server-alpha/a0.2.5-1004.jar",
    "a1.2.3": "server-alpha/a0.2.5-1004.jar",
    "a1.2.2b": "server-alpha/a0.2.4.jar",
    "a1.2.2a": "server-alpha/a0.2.4.jar",
    "a1.2.1_01": "server-alpha/a0.2.3.jar",
    "a1.2.1": "server-alpha/a0.2.3.jar",
    "a1.2.0_02": "server-alpha/a0.2.3.jar",
    "a1.2.0_01": "server-alpha/a0.2.2_01.jar",
    "a1.2.0": "server-alpha/a0.2.2.jar",
    "a1.1.2_01": "server-alpha/a0.2.1.jar",
    "a1.1.2": "server-alpha/a0.2.1.jar",
    "a1.1.0": "server-alpha/a0.2.1.jar",
    "a1.0.17_04": "server-alpha/a0.1.4.jar",
    "a1.0.17_02": "server-alpha/a0.1.4.jar",
    "a1.0.16": "server-alpha/a0.1.1-1707.jar",
    "a1.0.15": "server-alpha/a0.1.0.jar",
    "a1.0.14": "TODO: FIND",
    "a1.0.11": "TODO: FIND",
    "a1.0.5_01": "TODO: FIND",
    "a1.0.4": "TODO: FIND",

    "inf-20100618": "TODO: FIND",
    "c0.30_01c": "TODO: FIND",
    "c0.0.13a": "TODO: FIND",
    "c0.0.13a_03": "TODO: FIND",
    "c0.0.11a": "TODO: FIND",
    "rd-161348": "TODO: FIND",
    "rd-160052": "TODO: FIND",
    "rd-20090515": "TODO: FIND",
    "rd-132328": "TODO: FIND",
    "rd-132211": "TODO: FIND",
}

def has_omniarchive_url(version: str) -> bool:
    return version in OMNI_ARCHIVE_MAP


class Downloader:
    version_manifest: VersionManifest

    def __init__(self):
        self.version_manifest = self.get_version_manifest()

    @staticmethod
    def get_version_manifest() -> VersionManifest:
        """
        Gets and parses the version manifest (v2) from Mojang's servers.
        :return: Parsed VersionManifest object.
        """
        logger.info("Getting version manifest")
        request = requests.get(
            "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        )
        request.raise_for_status()

        manifest_json = request.json()

        def json_version_to_model(raw: dict) -> VersionManifestRelease:
            """
            Converts individual version records into VersionManifestRelease objects.

            :param raw: The raw object e.g.
            {
                'id': '1.8.9',
                'type': 'release',
                'url': 'https://piston-meta.mojang.com/v1/packages/d546f1707a3f2b7d034eece5ea2e311eda875787/1.8.9.json',
                'time': '2021-12-15T15:44:12+00:00',
                'releaseTime': '2015-12-03T09:24:39+00:00',
                'sha1': 'd546f1707a3f2b7d034eece5ea2e311eda875787',
                'complianceLevel': 0
            }

            :return: parsed VersionManifestRelease object.
            """

            return VersionManifestRelease(
                id=raw["id"],
                type=raw["type"],
                release_url=raw["url"],
                time=datetime.fromisoformat(raw["time"]),
                release_time=datetime.fromisoformat(raw["releaseTime"]),
                sha1=raw["sha1"],
                compliance_level=raw["complianceLevel"],
            )

        return VersionManifest(
            latest=VersionManifestLatestRelease(
                release=manifest_json["latest"]["release"],
                snapshot=manifest_json["latest"]["snapshot"],
            ),
            versions={
                release["id"]: json_version_to_model(release)
                for release in manifest_json["versions"]
                if release["id"] not in OMNI_ARCHIVE_MAP
               or OMNI_ARCHIVE_MAP[release["id"]] != "TODO: FIND"
            },
        )

    @lru_cache(maxsize=64)
    def get_release_manifest(self, id_: str) -> ReleaseManifest:
        """
        Gets and parses the manifest for a specific version.

        :param id_: The "id" value from the VersionManifest. e.g. "1.8.9"
        :return: Parsed ReleaseManifest
        """
        if id_ == "latest-release":
            id_ = self.version_manifest.latest.release
        elif id_ == "latest-snapshot":
            id_ = self.version_manifest.latest.snapshot

        release = self.version_manifest.versions[id_]

        url = release.release_url

        request = requests.get(url)
        request.raise_for_status()

        release_raw = request.json()

        if has_omniarchive_url(id_):
            return ReleaseManifest(
                java=Java(
                    component=JavaComponentEnum.jre_legacy,
                    major_version=8,
                ),
                server=ReleaseManifestServer(
                    sha1="N/A",
                    size=-1,
                    url=OMNI_ARCHIVE_BASE + OMNI_ARCHIVE_MAP[id_],
                ),
            )
        elif "server" in release_raw["downloads"]:
            return ReleaseManifest(
                java=Java(
                    component=release_raw["javaVersion"]["component"],
                    major_version=release_raw["javaVersion"]["majorVersion"],
                ),
                server=ReleaseManifestServer(
                    sha1=release_raw["downloads"]["server"]["sha1"],
                    size=release_raw["downloads"]["server"]["size"],
                    url=release_raw["downloads"]["server"]["url"],
                ),
            )
        raise RuntimeError("Unhandled version!")

if __name__ == "__main__":
    downloader = Downloader()
    with open("urls.txt", "w") as f:
        for version in downloader.version_manifest.versions.values():
            f.write(version.release_url + "\n")
