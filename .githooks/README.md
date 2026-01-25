# Git Hooks Setup

This repository uses Git hooks to automatically format code with Prettier before each commit.

## One-time Setup

After cloning the repository, run this command to enable the hooks:

```bash
git config core.hooksPath .githooks
```

That's it! The hooks will now run automatically before each commit.

## What it does

The `pre-commit` hook will:
- Automatically run `npx prettier --write .` before each commit
- Format all supported files (JS, CSS, HTML, JSON, Markdown)
- Stage the formatted files automatically
- Continue with the commit

## Skip the hook (if needed)

If you need to skip the formatting for a particular commit:

```bash
git commit --no-verify -m "your message"
```

## Troubleshooting

### Hook not running?

Check if the hooks path is set correctly:

```bash
git config core.hooksPath
# Should output: .githooks
```

### npx not found?

Make sure Node.js and npm are installed:
```bash
node --version
npm --version
```
