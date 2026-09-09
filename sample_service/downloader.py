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


class Downloader:
    version_manifest: VersionManifest
    def __init__(self):
        self.version_manifest = self.get_version_manifest()

    @staticmethod
    def get_version_manifest() -> VersionManifest:
        logger.info("Getting version manifest")
        request = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
        request.raise_for_status()

        manifest_json = request.json()

        def json_version_to_model(raw: dict) -> VersionManifestRelease:
            return VersionManifestRelease(
                id=raw["id"],
                type=raw["type"],
                release_url=raw["url"],
                time=datetime.fromisoformat(raw["time"]),
                release_time=datetime.fromisoformat(raw["releaseTime"]),
                sha1=raw["sha1"],
                compliance_level=raw["complianceLevel"]
            )

        return VersionManifest(
            latest=VersionManifestLatestRelease(
                release=manifest_json["latest"]["release"],
                snapshot=manifest_json["latest"]["snapshot"]
            ),
            versions={release["id"]: json_version_to_model(release) for release in manifest_json["versions"]}
        )

    @lru_cache(maxsize=64)
    def get_release_manifest(self, id_: str) -> ReleaseManifest:
        release = self.version_manifest.versions[id_]

        url = release.release_url

        request = requests.get(url)
        request.raise_for_status()

        release_raw = request.json()

        return ReleaseManifest(
            java=Java(
                component=release_raw["javaVersion"]["component"],
                major_version=release_raw["javaVersion"]["majorVersion"]
            ),
            server=ReleaseManifestServer(
                sha1=release_raw["downloads"]["server"]["sha1"],
                size=release_raw["downloads"]["server"]["size"],
                url=release_raw["downloads"]["server"]["url"]
            )
        )

if __name__ == '__main__':
    downloader = Downloader()
    release = downloader.get_release_manifest("1.8.9")
    print(release)