[2026-04-15 09:00] user:
We should keep the workbench lightweight and proposal-first. I think the recorder should default to propose mode and never rewrite all files.

[2026-04-15 09:02] assistant:
Agreed. I would treat that as a decision: proposal-first, with conservative apply only after confirmation.

[2026-04-15 09:05] user:
I also want a term for the intermediate normalized turn list. Let's call it transcript bundle for now, though it may still be a working hypothesis.

[2026-04-15 09:09] assistant:
Working hypothesis noted: `transcript bundle` is the normalized transcript artifact consumed by extraction and compare stages.

[2026-04-15 09:12] user:
One open question is whether README updates should ever be applied automatically, or whether they should stay proposal-only in v0.1.

[2026-04-15 09:15] assistant:
Important milestone: the tool has been framed as conversation-to-workbench, not as a generic meeting notes system.
