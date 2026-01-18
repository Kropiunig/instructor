# Migration Automation Setup

This document explains how to use the automated migration script for the v2 provider migration.

## Prerequisites

### 1. Install Graphite CLI

```bash
brew install withgraphite/tap/graphite
```

Or visit: https://graphite.dev/docs/installing-the-cli

### 2. Install Cursor CLI

```bash
curl https://cursor.com/install -fsS | bash
```

Make sure `~/.local/bin` is in your `PATH`. Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Verify Installations

```bash
gt --version
cursor-agent --version
```

## Configuration

### Cursor CLI Permissions

The `.cursor/cli-config.json` file configures what operations the Cursor agent can perform:

```json
{
  "version": 1,
  "permissions": {
    "allow": [
      "Shell(git)",
      "Shell(gt)",
      "Shell(pytest)",
      "Write(instructor/**/*)",
      "Write(tests/**/*)",
      ...
    ],
    "deny": [
      "Shell(rm -rf /)",
      "Write(.env)",
      ...
    ]
  }
}
```

This file is already set up in `.cursor/cli-config.json`.

## Usage

### Run the Migration Script

```bash
./work_through_migration.sh
```

This will:
1. Check for required dependencies (gt, cursor-agent)
2. Show current Graphite stack status
3. Loop through migration plan sections
4. For each section:
   - Call cursor-agent to work on the next unchecked task
   - Create/use Graphite branches (e.g., `migration/openai`)
   - Make commits with conventional commit messages
   - Create migration notes in `refactor_plan/theme2_architecture/migration_notes/`

### Custom Plan File

```bash
./work_through_migration.sh custom_plan.md
```

## Migration Workflow

### Per Provider

1. **Branch Creation**: `gt branch create migration/<provider-name>`
2. **Implementation**: cursor-agent works through tasks
3. **Commits**: Multiple commits as tasks are completed
4. **Notes**: Creates `migration_notes/<provider>_notes.md`
5. **Testing**: Runs provider-specific tests
6. **PR Submission**: `gt stack submit --reviewers jxnl,ivanleomk`

### Stack Management

View your current stack:

```bash
gt log short
```

Submit completed work:

```bash
gt stack submit --reviewers jxnl,ivanleomk
```

Resume if interrupted:

```bash
cursor-agent resume
```

## What the Script Does

### For Each Iteration:

1. Reads `refactor_plan/theme2_architecture/v2_provider_migration_plan.md`
2. Finds the next unchecked task (`- [ ]`)
3. Works on that specific task
4. Checks it off (`- [x]`) when complete
5. Commits changes with descriptive messages
6. Creates/updates migration notes

### Migration Notes

Stored in `refactor_plan/theme2_architecture/migration_notes/{provider}_notes.md`:

- Implementation details
- Test results
- Issues encountered
- Deviations from plan
- Follow-up tasks

### Safety Features

- Max 50 iterations (configurable)
- Permissions controlled via `.cursor/cli-config.json`
- Dangerous operations (rm -rf, etc.) are denied
- All changes are versioned via git/Graphite

## Monitoring Progress

### Check Plan Status

```bash
grep -E "^- \[(x| )\]" refactor_plan/theme2_architecture/v2_provider_migration_plan.md | head -20
```

### View Migration Notes

```bash
ls -la refactor_plan/theme2_architecture/migration_notes/
cat refactor_plan/theme2_architecture/migration_notes/openai_notes.md
```

### View Graphite Stack

```bash
gt log short
gt status
```

## Stopping and Resuming

### Stop the Script

Press `Ctrl+C` to stop gracefully.

### Resume Work

The script is idempotent - just run it again:

```bash
./work_through_migration.sh
```

It will find the next unchecked task and continue.

## Troubleshooting

### cursor-agent not found

```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.zshrc
```

### gt not found

```bash
brew install withgraphite/tap/graphite
```

### Permission denied

Check `.cursor/cli-config.json` has the required permissions.

### Script loops on same task

The task may not be getting checked off. Check the migration plan file manually and mark completed tasks with `- [x]`.

## Example Run

```bash
$ ./work_through_migration.sh

Using plan file: refactor_plan/theme2_architecture/v2_provider_migration_plan.md

Current Graphite stack:
main

=========================================
Iteration 1
=========================================

Calling cursor-agent with prompt...

[cursor-agent works on next task...]
[creates files, runs tests, commits...]

Iteration 1 completed

=========================================
Iteration 2
=========================================

...
```

## Notes

- The script runs in non-interactive mode (`cursor-agent -p --force`)
- Changes are applied automatically (be in a safe branch!)
- All git operations use Graphite for stack management
- PRs are created via `gt stack submit` (not automatic)
