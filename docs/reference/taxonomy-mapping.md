# Taxonomy mapping

How this site's sections, statuses, identifiers and equipment map to a
ServiceNow knowledge base's categories, workflow states and keywords when
the runbooks are [exported](kb-export-format.md). The mapping is made by
the export from `structure.toml`, the runbooks' front matter and the
inventory, and the tests compare these tables with what it makes.

## Categories

Every exported page is filed under its section's title, and every section
under one top category, so the knowledge base's own categories are left
as they are:

| Site section | Folder | Knowledge-base category |
| --- | --- | --- |
| Audio-visual | `runbooks/av/` | Classroom technology > Audio-visual |
| Network | `runbooks/network/` | Classroom technology > Network |
| Peripherals | `runbooks/peripherals/` | Classroom technology > Peripherals |
| Account access | `runbooks/accounts/` | Classroom technology > Account access |
| Procedures | `procedures/` | Classroom technology > Procedures |

A section has a category only when some page in it is exported: Procedures
has one for the escalation matrix, and the other sections have none. A
new runbook category in `structure.toml` becomes a new category at the
next export.

## Status and workflow state

| Runbook `status` | Article `workflow_state` |
| --- | --- |
| `draft` | `draft` |
| `current` | `published` |
| `retired` | `retired` |

A runbook becomes `current` when a second author has followed it on real
equipment ([authoring conventions](../contributing/authoring-conventions.md)),
and only then is its article published. Every runbook is a draft today,
so every article arrives as one. A retired runbook is still exported, as a
retired article, so a ticket that quotes its identifier still finds it and
the number is never given to another. A page that is not a runbook has no
status and arrives as a draft, for the knowledge base's reviewers to
publish.

## Identifiers and keywords

| On the site | In the knowledge base |
| --- | --- |
| The runbook's identifier, `RB-AV-001` | the first keyword in `meta`, and the article's last line |
| The runbook's `title` | `short_description`, the article's title |
| Each `equipment` id | its name in the inventory, a keyword in `meta` (`laser-projector` is `Laser projector`) |
| The runbook's identifier, or another page's path | its `sys_id`, made from it and the knowledge base |
| A link to another runbook | a link to that runbook's article |

The knowledge base's own article number is given by the instance and
nowhere on the site; tickets quote the runbook's identifier, which a
search of the knowledge base finds through `meta`. The equipment names
let a search for the equipment in a room (`Ceiling microphone array`)
find the runbooks for it.
