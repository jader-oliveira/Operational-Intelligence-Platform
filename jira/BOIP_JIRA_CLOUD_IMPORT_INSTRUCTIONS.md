# BOIP Jira Cloud CSV Import Instructions

Use only this CSV:

`BOIP_JIRA_CLOUD_IMPORT_FIXED.csv`

Do not use either of the previous Jira CSV files.

## Target

This file follows Atlassian's current **Jira Cloud company-managed project** hierarchy-import method.

## Validated contents

- 260 total work items
- 20 Epics
- 160 Stories
- 80 Sub-tasks
- Unique Work item IDs: validated
- Every Parent exists: validated
- Every parent occurs before its child: validated
- Hierarchy order: Epics, then Stories, then Sub-tasks
- Encoding: UTF-8
- Delimiter: comma
- Multiline content: quoted
- Multi-value labels: repeated Labels columns

## Before importing

1. Use a **company-managed** Jira project.
2. Confirm the project has these work types:
   - Epic
   - Story
   - Sub-task
3. Enable sub-tasks in Jira.
4. If the Parent field is missing in the importer, add the Linked Issues field to the relevant project screens.
5. Import through Jira administration:
   - Settings
   - System
   - External system import
   - Switch to the old experience
   - CSV

## Field mapping

| CSV field | Jira field |
| --- | --- |
| Work item ID | Work item ID or Issue ID |
| Work type | Work type or Issue type |
| Summary | Summary |
| Description | Description |
| Parent | Parent |
| Priority | Priority |
| Labels | Labels |
| Labels | Labels |
| Labels | Labels |

Do not map any column to Epic Link or Epic Name.

## Value mapping

Map the CSV values as follows:

- Epic -> your project's Epic work type
- Story -> your project's Story work type
- Sub-task -> your project's Sub-task work type
- Highest, High and Medium -> matching Jira priorities

If the project uses different names, explicitly map each CSV value in the import wizard.

## First safe test

In the import wizard, stop before the final import and verify that Jira recognizes:

- 20 Epics
- 160 Stories
- 80 Sub-tasks
- Parent as a mapped field

After import, open one Story and one Sub-task and verify that their Parent fields are populated.
