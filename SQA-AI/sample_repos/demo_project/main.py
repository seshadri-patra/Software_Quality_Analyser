"""
Demo Project - Main Module
A simple application to demonstrate SQA-AI analysis
"""

from .utils import calculate_sum, format_message
from .complex import ComplexProcessor


def main():
    """Main entry point for the demo application"""
    print("Welcome to the Demo Application")
    
    # Simple calculation
    result = calculate_sum(10, 20)
    print(format_message(f"Sum: {result}"))
    
    # Complex processing
    processor = ComplexProcessor()
    data = [1, 2, 3, 4, 5]
    processed = processor.process(data)
    print(f"Processed data: {processed}")
    
    return 0


def validate_input(value):
    """Validate user input"""
    if value is None:
        return False
    if not isinstance(value, (int, float, str)):
        return False
    return True


def get_user_name():
    """Get user name with validation"""
    name = input("Enter your name: ")
    if validate_input(name):
        return name.strip()
    return "Anonymous"


if __name__ == "__main__":
    main()