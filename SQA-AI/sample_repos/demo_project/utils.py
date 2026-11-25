"""
Demo Project - Utility Functions
Helper functions for the demo application
"""

from typing import List, Any, Optional


def calculate_sum(a: int, b: int) -> int:
    """
    Calculate the sum of two numbers
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    return a + b


def calculate_average(numbers: List[float]) -> float:
    """
    Calculate average of a list of numbers
    
    Args:
        numbers: List of numbers
    
    Returns:
        Average value
    """
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def format_message(msg: str, prefix: str = "INFO") -> str:
    """
    Format a message with prefix
    
    Args:
        msg: Message to format
        prefix: Prefix to add
    
    Returns:
        Formatted message
    """
    return f"[{prefix}] {msg}"


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    if b == 0:
        return default
    return a / b


def flatten_list(nested: List[List[Any]]) -> List[Any]:
    """Flatten a nested list"""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result