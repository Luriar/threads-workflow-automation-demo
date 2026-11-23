import tempfile
import unittest
from pathlib import Path
from review_queue import Incoming,ReviewQueue,evaluate


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.queue=ReviewQueue(Path(self.tmp.name)/"queue.sqlite")

    def tearDown(self):
        self.queue.close()
        self.tmp.cleanup()

    def test_sensitive_context_escalates(self):
        self.assertEqual(evaluate("refund, please")[0],"escalated")
        self.assertEqual(evaluate("Looks interesting")[0],"needs_review")

    def test_deduplication(self):
        item=Incoming("x","Hello")
        self.assertEqual(self.queue.ingest([item,item]),{"queued":1,"duplicate":1})
        self.assertEqual(len(self.queue.inbox()),1)

    def test_human_review_required(self):
        self.queue.ingest([Incoming("x","Hello"),Incoming("y","complaint")])
        self.assertEqual(self.queue.inbox()[0]["state"],"needs_review")
        self.assertTrue(self.queue.decision("x","human",True))
        self.assertTrue(self.queue.decision("y","human",False))
        self.assertEqual(self.queue.inbox()[0]["state"],"approved_draft")
        self.assertEqual(self.queue.inbox()[1]["state"],"rejected")
        self.assertEqual(len(self.queue.audit()),4)

    def test_repeat_review_prevented(self):
        self.queue.ingest([Incoming("x","Hello")])
        self.queue.decision("x","human",True)
        with self.assertRaises(ValueError):
            self.queue.decision("x","human",True)

    def test_invalid_batch_rolls_back(self):
        with self.assertRaises(ValueError):
            self.queue.ingest([Incoming("x","Hello"),Incoming("y","")])
        self.assertEqual(self.queue.inbox(),[])

    def test_unknown_id_safe(self):
        self.assertFalse(self.queue.decision("missing","human",True))


if __name__=="__main__":
    unittest.main()
