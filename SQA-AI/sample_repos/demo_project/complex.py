"""
Demo Project - Complex Module
Intentionally complex code to demonstrate SQA-AI detection
WARNING: This code has intentional code smells for demo purposes
"""

class ComplexProcessor:
    def __init__(self):
        self.data = []
        self.cache = {}
        self.results = []
        self.errors = []
        self.warnings = []
        self.config = {}
        self.state = None
        self.counter = 0
    
    def process(self, data, option1=None, option2=None, option3=None, option4=None, option5=None, option6=None):
        result = []
        for item in data:
            if item is None:
                self.errors.append("null item")
                continue
            if isinstance(item, int):
                if item < 0:
                    if item < -100:
                        result.append(item * -1 * 2)
                    elif item < -50:
                        result.append(item * -1 * 1.5)
                    elif item < -10:
                        result.append(item * -1)
                    else:
                        result.append(0)
                elif item > 0:
                    if item > 100:
                        if item > 1000:
                            result.append(item / 10)
                        else:
                            result.append(item / 5)
                    elif item > 50:
                        result.append(item / 2)
                    elif item > 10:
                        result.append(item)
                    else:
                        result.append(item * 2)
                else:
                    result.append(0)
            elif isinstance(item, str):
                if len(item) > 100:
                    result.append(item[:100])
                elif len(item) > 50:
                    result.append(item[:50])
                else:
                    result.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if sub is not None:
                        result.append(sub)
            elif isinstance(item, dict):
                for k, v in item.items():
                    if v is not None:
                        result.append(v)
            else:
                result.append(str(item))
        self.results = result
        return result
    
    def validate_and_transform_data_with_multiple_conditions_and_side_effects(self, data, strict_mode=False, allow_nulls=False, max_length=1000, min_length=0, transform_type="default"):
        validated = []
        for i, item in enumerate(data):
            if item is None:
                if allow_nulls:
                    validated.append(None)
                else:
                    self.errors.append(f"Null at index {i}")
            elif isinstance(item, str):
                if len(item) > max_length:
                    if strict_mode:
                        self.errors.append(f"Too long at {i}")
                    else:
                        validated.append(item[:max_length])
                elif len(item) < min_length:
                    if strict_mode:
                        self.errors.append(f"Too short at {i}")
                    else:
                        validated.append(item.ljust(min_length))
                else:
                    validated.append(item)
            else:
                validated.append(item)
        return validated


def badly_named_function_that_does_too_many_things(x, y, z, a, b, c, d, e, f, g):
    result = 0
    if x > 0:
        result += x
    if y > 0:
        result += y
    if z > 0:
        result += z
    if a > 0:
        result += a * 2
    if b > 0:
        result += b * 3
    if c > 0:
        result += c * 4
    if d > 0:
        result -= d
    if e > 0:
        result -= e
    if f > 0:
        result *= f
    if g > 0:
        result /= g if g != 0 else 1
    return result


def deeply_nested_logic(value):
    if value is not None:
        if isinstance(value, int):
            if value > 0:
                if value < 100:
                    if value % 2 == 0:
                        if value % 4 == 0:
                            return "divisible by 4"
                        else:
                            return "even"
                    else:
                        return "odd"
                else:
                    return "large"
            else:
                return "non-positive"
        else:
            return "not int"
    else:
        return "null"
    