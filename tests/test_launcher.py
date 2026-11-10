import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import launcher

class LauncherTests(unittest.TestCase):
    def archive(self,root,name):
        target=root/'engines/downloads/stockfish-macos-universal.tar.gz'
        target.parent.mkdir(parents=True)
        with tarfile.open(target,'w:gz') as tar:
            member=tarfile.TarInfo(name);member.size=4;tar.addfile(member,io.BytesIO(b'test'))
    def test_mac_engine_extract_and_permission(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.archive(root,'stockfish/stockfish-macos-universal')
            with patch.object(launcher,'ROOT',root),patch.object(launcher.sys,'platform','darwin'),patch.dict(launcher.os.environ,{},clear=True):
                launcher.prepare_mac_engine()
                engine=root/'engines/stockfish-macos/stockfish/stockfish-macos-universal'
                self.assertEqual(engine.read_bytes(),b'test')
                launcher.prepare_mac_engine()
    def test_reject_archive_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.archive(root,'../../outside')
            with patch.object(launcher,'ROOT',root),patch.object(launcher.sys,'platform','darwin'),patch.dict(launcher.os.environ,{},clear=True):
                with self.assertRaises(ValueError):launcher.prepare_mac_engine()
            self.assertFalse((root/'outside').exists())
    def test_running_service_reused(self):
        with patch.object(launcher,'health',return_value=True),patch.object(launcher,'open_home') as opened,patch.object(launcher,'prepare_environment') as prepare,patch.object(launcher.sys,'argv',['launcher.py']):
            self.assertEqual(launcher.main(),0);opened.assert_called_once();prepare.assert_not_called()
    def test_lock_released(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'lock';first=launcher.acquire_lock(path)
            self.assertIsNotNone(first)
            second=launcher.acquire_lock(path);self.assertIsNone(second)
            first.close()
            third=launcher.acquire_lock(path);self.assertIsNotNone(third);third.close()
