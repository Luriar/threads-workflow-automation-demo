import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from demo import Incoming,propose

class ReviewTests(unittest.TestCase):
    def test_requires_review_and_deduplicates(self):
        a=propose([Incoming("a","Thanks"),Incoming("a","Thanks"),
                   Incoming("b","complaint")])
        self.assertEqual(a,[("a","review_before_any_reply"),("b","manual_review")])

if __name__ == "__main__":
    unittest.main()
