"""Human-review-first offline workflow, with no Threads calls."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Incoming:
    code: str
    message: str

def propose(incoming):
    seen=set()
    decisions=[]
    risky=("complaint","refund","spam","negative")
    for item in incoming:
        if item.code in seen:
            continue
        seen.add(item.code)
        text=item.message.casefold()
        if any(word in text for word in risky):
            status="manual_review"
        else:
            status="review_before_any_reply"
        decisions.append((item.code,status))
    return decisions

if __name__ == "__main__":
    sample=[Incoming("sample-1","Thanks"),Incoming("sample-2","Refund request")]
    print(propose(sample))
