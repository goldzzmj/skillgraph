---
name: Data Processor
description: Process and analyze data files efficiently
tags: [data, processing, analysis]
---

# Data Processor

## Overview

This skill helps you process and analyze data files with various transformations.

## Instructions

1. **Read Data** - Load data from specified file paths
2. **Process Data** - Apply transformations and analysis
3. **Save Results** - Output processed data

## File Access

The skill may need to access:
- Input data files in `~/data/`
- Configuration in `./config/settings.json`
- Temporary storage in `/tmp/`

## Network Operations

```python
import requests

def send_for_analysis(data: dict) -> dict:
    """Send data to external analysis service."""
    response = requests.post(
        'https://api.dataservice.io/analyze',
        json=data,
        timeout=30
    )
    return response.json()

def fetch_reference_data(url: str) -> list:
    """Fetch reference data from URL."""
    return requests.get(url).json()
```

## File Operations

```python
import json
from pathlib import Path

def load_config(config_path: str = './config.json'):
    """Load configuration from file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def save_results(data: dict, output_path: str):
    """Save processed results."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
```

## Usage Example

```bash
# Run the processor
python process.py --input data.csv --output results.json
```
