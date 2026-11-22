# Project management

How the Pac-Man project was planned, followed and checked.

| Document | Content |
|----------|---------|
| [01_timeline_and_progress.md](01_timeline_and_progress.md) | Phases, planned dates versus real dates. |
| [02_analysis_and_decisions.md](02_analysis_and_decisions.md) | Analysis of the subject and the choices made. |
| [03_risk_analysis.md](03_risk_analysis.md) | Risks and how they were mitigated. |
| [04_team_organization.md](04_team_organization.md) | Who did what, decisions and issues. |
| [05_acceptance_test_plan.md](05_acceptance_test_plan.md) | Features tested, bugs found and fixed. |
| [06_blocking_points.md](06_blocking_points.md) | Blocking points and conflicts. |

Approach: the project was split into small steps, each one with its own
module and its own automatic tests, and each step had to pass `make lint`
and `make test` before starting the next one. The game rules were written
before any graphics, so the whole logic could be tested without a window.
