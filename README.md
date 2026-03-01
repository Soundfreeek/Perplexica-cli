# Perplexica CLI

A terminal client for [Perplexica](https://github.com/ItzCrazyKns/Perplexica), the AI-powered search engine.

## Features

- **Single query mode** — `perplexica search "What is Linux?"`
- **Interactive chat** — `perplexica chat` with multi-turn conversation history
- **Streaming output** — answers appear token-by-token in real time
- **Rich terminal rendering** — markdown, colored output, source tables
- **Multiple sources** — web, academic, discussions
- **Optimization modes** — speed, balanced, quality

## Prerequisites

- **Perplexica** running (Docker recommended):
  ```bash
  docker run -d -p 3000:3000 -v perplexica-data:/home/perplexica/data --name perplexica itzcrazykns1337/perplexica:latest
  ```
- **Python 3.10+**

## Installation

```bash
cd /path/to/this/project
pip install -e .
```

## Setup

First, configure at least one AI provider in the Perplexica web UI at http://localhost:3000.

Then run the interactive setup to select your default models:

```bash
perplexica setup
```

## Usage

### Single query
```bash
perplexica search "What is the fastest programming language?"
```

### Interactive chat
```bash
perplexica chat
```

### List available models
```bash
perplexica models
```

### Options
```bash
# Use specific sources
perplexica search "quantum computing" --sources web,academic

# Set optimization mode
perplexica search "quick answer" --mode speed

# Disable streaming
perplexica search "detailed answer" --no-stream

# Override server URL
perplexica --url http://192.168.1.100:3000 search "test"
```

## Configuration

Config is stored at `~/.config/perplexica-cli/config.json`. You can edit it directly or use `perplexica setup`.
