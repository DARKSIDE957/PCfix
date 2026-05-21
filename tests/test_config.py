import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import core


class TestConfig(unittest.TestCase):
    def test_config_saved_under_localappdata(self):
        cfg = core.load_config()
        cfg["_test_key"] = "ok"
        self.assertTrue(core.save_config(cfg))
        path = core._config_path()
        self.assertTrue(path.lower().endswith(os.path.join("pcfix", "config.json").lower().replace("/", os.sep)))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("_test_key"), "ok")
        data.pop("_test_key", None)
        core.save_config(data)


if __name__ == "__main__":
    unittest.main()
