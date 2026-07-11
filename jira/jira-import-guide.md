# Jira CSV Import Guide

## Files

- `boip_jira_import.csv`: complete hierarchy.
- `boip_epics.csv`: epics only, useful for a two-pass import.

## Backlog size

- Epics: 20
- Stories: 160
- Sub-tasks: 80
- Total issues: 260

## Recommended import mapping

| CSV column | Jira field |
| --- | --- |
| Issue ID | Issue ID |
| Issue Type | Issue Type |
| Summary | Summary |
| Description | Description |
| Priority | Priority |
| Labels | Labels |
| Epic Name | Epic Name |
| Epic Link | Epic Link, when your Jira importer supports name mapping |
| Parent ID | Parent or Parent ID |
| Story Points | Story Points |
| Component/s | Components |
| Acceptance Criteria | Map to an Acceptance Criteria custom field, or append to Description |
| Dependencies | Map to a text field; convert to issue links after import if required |
| Phase | Fix Version, custom Phase field, or label |
| Suggested Owner Role | Custom text field |
| Definition of Done | Custom multiline field, or append to Description |

## Hierarchy method

The CSV includes numeric `Issue ID` and `Parent ID` values. Map both during import. This is the preferred way to create sub-task relationships and, in Jira configurations that support it, story-to-epic relationships.

If your Jira instance does not allow stories to use `Parent ID` for epics:

1. Import `boip_epics.csv`.
2. Export or note the new epic keys.
3. Replace the `Epic Link` values in the full CSV with those epic keys.
4. Import only Story and Sub-task rows.
5. Map `Parent ID` for sub-tasks.

## Important checks before import

- Confirm the exact issue-type name for `Sub-task`.
- Confirm whether your Jira uses `Parent`, `Parent ID`, or `Epic Link`.
- Confirm the Story Points field is available on the selected project.
- Create any custom multiline fields before import, or merge their text into Description.
- Test with one epic and two stories in a sandbox project first.
