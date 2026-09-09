from enum import Enum

import requests
from pydantic import BaseModel
from datetime import datetime

import logging

logger = logging.getLogger("minecraft.downloader")

class LatestRelease(BaseModel):
    release: str
    snapshot: str

class ReleaseTypeEnum(str, Enum):
    release = "release"
    snapshot = "snapshot"
    old_beta = "old_beta"
    old_alpha = "old_alpha"

class Release(BaseModel):
    id: str
    type: ReleaseTypeEnum
    release_url: str
    time: datetime
    release_time: datetime
    sha1: str
    compliance_level: int

class VersionManifest(BaseModel):
    latest: LatestRelease
    versions: list[Release]

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

        def json_version_to_model(raw: dict) -> Release:
            return Release(
                id=raw["id"],
                type=raw["type"],
                release_url=raw["url"],
                time=datetime.fromisoformat(raw["time"]),
                release_time=datetime.fromisoformat(raw["releaseTime"]),
                sha1=raw["sha1"],
                compliance_level=raw["complianceLevel"]
            )

        return VersionManifest(
            latest=LatestRelease(
                release=manifest_json["latest"]["release"],
                snapshot=manifest_json["latest"]["snapshot"]
            ),
            versions=[json_version_to_model(release) for release in manifest_json["versions"]]
        )


if __name__ == '__main__':
    downloader = Downloader()
    print(downloader.version_manifest)