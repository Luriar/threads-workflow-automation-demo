"""Offline human-in-the-loop response queue. Never publishes social messages."""
from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Incoming:
    code: str
    content: str


def evaluate(message: str) -> tuple[str, str]:
    """Example-only safety triage; manual sign-off is required in every case."""
    risk=("refund","complaint","spam","negative","unhappy")
    if any(term in message.casefold() for term in risk):
        return "escalated","potentially sensitive context"
    return "needs_review","human must check the context"


class ReviewQueue:
    def __init__(self,path: str | Path = ":memory:"):
        self.db=sqlite3.connect(str(path))
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS inbox(
                code TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                state TEXT NOT NULL,
                reason TEXT NOT NULL,
                reviewer TEXT
            );
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL
            );
        """)
        self.db.commit()

    def ingest(self,events: list[Incoming]) -> dict:
        outcomes={"queued":0,"duplicate":0}
        with self.db:
            for event in events:
                if not event.code.strip() or not event.content.strip():
                    raise ValueError("code and content required")
                state,reason=evaluate(event.content)
                cur=self.db.execute("""
                    INSERT OR IGNORE INTO inbox(code,content,state,reason)
                    VALUES (?,?,?,?)
                """,(event.code,event.content,state,reason))
                if cur.rowcount:
                    outcomes["queued"]+=1
                    self.db.execute("INSERT INTO audit(code,action,actor) VALUES (?,?,'system')",
                                    (event.code,state))
                else:
                    outcomes["duplicate"]+=1
        return outcomes

    def decision(self,code: str,reviewer: str,approve: bool) -> bool:
        if not reviewer.strip():
            raise ValueError("reviewer name required")
        state="approved_draft" if approve else "rejected"
        with self.db:
            current=self.db.execute("SELECT state FROM inbox WHERE code=?",(code,)).fetchone()
            if current is None:
                return False
            if current["state"] not in ("needs_review","escalated"):
                raise ValueError("item already decided")
            self.db.execute("UPDATE inbox SET state=?,reviewer=? WHERE code=?",
                            (state,reviewer,code))
            self.db.execute("INSERT INTO audit(code,action,actor) VALUES (?,?,?)",
                            (code,state,reviewer))
        return True

    def inbox(self) -> list[dict]:
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM inbox ORDER BY code"
        )]

    def audit(self) -> list[dict]:
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM audit ORDER BY id"
        )]

    def close(self):
        self.db.close()


if __name__=="__main__":
    queue=ReviewQueue()
    try:
        queue.ingest([
            Incoming("fictional-01","Can you share more information?"),
            Incoming("fictional-02","I want a refund"),
            Incoming("fictional-01","Can you share more information?")
        ])
        queue.decision("fictional-01","sample-reviewer",True)
        print(json.dumps({
            "inbox":queue.inbox(),"audit":queue.audit(),
            "notice":"No social network messages were sent."
        },indent=2))
    finally:
        queue.close()
