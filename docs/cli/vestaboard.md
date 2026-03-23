---
title: Vestaboard CLI
description: Send text or a full character matrix to a Vestaboard using the Cloud API.
---

# Vestaboard CLI

This CLI lets you send messages to a Vestaboard using the Vestaboard Cloud API.

It supports:

- **Text messages**: send plain text with `text`
- **Character matrices**: send the full board state with `characters` (a matrix of integer codes)

## Install

The CLI is included with this package.

```bash
uv pip install -e ".[dev]"
```

## Set your token

Create a Cloud API token in the Vestaboard app, then set it as an environment variable:

```bash
export VESTABOARD_TOKEN="your-token-here"
```

## Send text

Send a plain text message:

```bash
vestaboard send-text "Hello World"
```

Override quiet hours:

```bash
vestaboard send-text "Hello World" --forced
```

## Send a character matrix

The flagship Vestaboard matrix is **6 rows x 22 columns**.

Create a JSON file (example `message.json`):

```json
{
  "characters": [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 8, 5, 12, 12, 15, 0, 23, 15, 18, 12, 4, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  ]
}
```

Send it:

```bash
vestaboard send-matrix message.json
```

Read the JSON from stdin:

```bash
cat message.json | vestaboard send-matrix -
```

If you are sending a different board size (like a Note Array), you can skip the dimension check:

```bash
vestaboard send-matrix message.json --no-dimension-check
```

## Format text into a matrix (VBML)

You can format text into a character matrix using the public VBML formatter:

```bash
vestaboard format "Hello World"
```

Save the result to a file:

```bash
vestaboard format "Hello World" --output matrix.json
```

## Use via `instructor`

If you already use the `instructor` CLI, the same commands are available under:

```bash
instructor vestaboard --help
```

