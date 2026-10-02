"""
Tests related to the downloader

Author: Quintin Dunn
Date: 10/01/2026
"""

import unittest

import sys

from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from sample_module.downloader import Downloader, VersionManifestReleaseTypeEnum


class TestDownloader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Sets up the tests to not get VersionManifest every single time.
        """

        cls.downloader = Downloader()
        cls.releases = cls.downloader.version_manifest.latest.release

    def test_get_version_manifest(self):
        """
        Tests the download successfully got the version manifest. The version manifest it gotten
        on Downloader.__init__()
        """

        self.assertIsNotNone(self.downloader.version_manifest)

    def test_get_latest_release(self):
        """
        Tests that the downloader's latest release, snapshot does truly match the latest release, snapshot
        """

        latest_release = None
        latest_snapshot = None
        for version in self.downloader.version_manifest.versions.values():
            if (
                latest_release is None
                and version.type == VersionManifestReleaseTypeEnum.release
            ):
                latest_release = version
            if (
                latest_snapshot is None
                and version.type == VersionManifestReleaseTypeEnum.snapshot
            ):
                latest_snapshot = version
            if latest_snapshot is not None and latest_release is not None:
                break
        self.assertIsNotNone(latest_release, "Couldn't find latest release")
        self.assertIsNotNone(latest_snapshot, "Couldn't find latest snapshot")

        latest_release_id = self.downloader.version_manifest.latest.release
        latest_snapshot_id = self.downloader.version_manifest.latest.snapshot

        self.assertEqual(latest_release_id, latest_release.id)
        self.assertEqual(latest_snapshot_id, latest_snapshot.id)

    def test_get_version(self):
        """
        Tests getting specific versions.
        """

        v1_8_9 = self.downloader.get_release_manifest("1.8.9")
        self.assertEqual(v1_8_9.java.major_version, 8)
        v_26_1 = self.downloader.get_release_manifest("26.1")
        self.assertEqual(v_26_1.java.major_version, 25)

        v_1_0 = self.downloader.get_release_manifest("1.0")
        self.assertEqual(v_1_0.java.major_version, 8)

        v_rd_132211 = self.downloader.get_release_manifest("rd-132211")
        self.assertEqual(v_rd_132211.java.major_version, 8)
