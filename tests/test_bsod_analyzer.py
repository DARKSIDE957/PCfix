import unittest
from modules import core

class TestBSODHeuristics(unittest.TestCase):
    def test_known_bugchecks(self):
        cases = [
            ("0x00000124", None, "WHEA error", "lmv output", "hardware"),
            ("0x00000050", None, "memory_corruption", "lmv output", "memory"),
            ("0x0000009F", None, "ndis", "lmv output", "driver"),
            ("0x000000D1", None, "netio", "lmv output", "driver"),
            ("0x0000007A", None, "storport", "lmv output", "storage"),
        ]
        for code, prob, st, lm, expect in cases:
            res = core.classify_root_cause(code, prob, st, lm)
            self.assertEqual(res["category"], expect)
            self.assertGreaterEqual(res["confidence"], 0.85)

    def test_probably_driver_boost(self):
        res = core.classify_root_cause("0x0000003B", "nvlddmkm.sys", "", "Loaded symbol image file: nvlddmkm.sys")
        self.assertEqual(res["category"], "driver")
        self.assertGreaterEqual(res["confidence"], 0.9)

    def test_bulk_generated(self):
        bugchecks = ["0x00000124", "0x00000050", "0x0000009F", "0x000000D1", "0x0000007A"]
        drivers = ["nvlddmkm.sys", "atikmdag.sys", "rtwlane.sys", "iaStorA.sys", "Unknown.sys"]
        total = 0
        for code in bugchecks:
            for drv in drivers:
                res = core.classify_root_cause(code, drv if "Unknown" not in drv else None, drv, f"Loaded symbol image file: {drv}")
                self.assertIn(res["category"], ("hardware", "memory", "driver", "storage", "unknown"))
                total += 1
        self.assertGreaterEqual(total, 25)

if __name__ == "__main__":
    unittest.main()

