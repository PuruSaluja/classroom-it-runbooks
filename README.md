# Classroom IT Runbooks

Runbooks, a room inventory and support procedures for the technology in a
campus's classrooms (projectors, displays, audio, control systems, network,
peripherals and account access), written in Markdown, with Python tools that
check them and export them to ServiceNow's knowledge base.

> **Status:** in progress. The repository's layout and tooling are in place;
> the content and the tools below are built in order.

## What this repository is, and is not

The runbooks are written as a student technician on a classroom support team
would use them: one fault, its symptoms, the checks in order, the fix, and
when to hand it on. They are general to the equipment, not copied from any
institution's knowledge base.

**The room inventory is illustrative.** Buildings, room numbers and the
equipment in each room are made up to resemble a large campus; they are not
any university's real inventory, which would not be published.

What the repository can show is what it contains: how many rooms and
runbooks there are, and whether every piece of equipment in every room has a
runbook, which its tools check. It cannot show what happened when runbooks
like these were used by a real support team (fewer repeat tickets, faster
onboarding); where those are mentioned they are reported, not demonstrated
here.

## Parts

| Part | State |
| --- | --- |
| Repository scaffold and information architecture | in progress |
| Room inventory: 200+ classrooms with equipment profiles | to come |
| Runbook template and authoring conventions | to come |
| AV runbooks: projectors, displays, audio, cabling, control systems | to come |
| Network, peripheral and account-access runbooks | to come |
| Escalation matrix, shift handoff and the onboarding path for new technicians | to come |
| Validator: required sections, room-to-runbook coverage, dead cross-links | to come |
| ServiceNow knowledge-base export and taxonomy mapping | to come |
| MkDocs Material site, with the validator in CI | to come |
| Published site | to come |

## Development

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -c constraints.txt -e ".[dev]"   # bin/ on Linux and macOS
pytest
ruff check . && ruff format --check .
```

## License

MIT; see [LICENSE](LICENSE).
