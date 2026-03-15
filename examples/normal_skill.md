---
name: Code Review Helper
description: A helpful skill for code review and quality analysis
tags: [code, review, quality, best-practices]
---

# Code Review Helper

## When to Use

Use this skill when you need to:
- Review code for quality and best practices
- Identify potential bugs or issues
- Suggest improvements for readability

## Instructions

1. **Analyze Structure** - Check the overall code structure and organization
2. **Check Patterns** - Look for common anti-patterns
3. **Suggest Improvements** - Provide actionable recommendations

## Example Usage

```python
def calculate_sum(numbers: list) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

def calculate_average(numbers: list) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0
    return calculate_sum(numbers) / len(numbers)
```

## Best Practices

- Follow PEP 8 style guidelines
- Use type hints for better code clarity
- Write docstrings for functions and classes
- Keep functions small and focused
