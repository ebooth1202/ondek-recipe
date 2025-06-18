"""
Utility functions for the Ondek Recipe application
"""

from fractions import Fraction
from typing import Union

# Fraction utility functions
def parse_fraction(value: str) -> float:
    """
    Parse a string representation of a fraction or mixed number into a float

    Examples:
    - "1/2" -> 0.5
    - "1 1/2" -> 1.5
    - "2" -> 2.0
    """
    value = value.strip()

    try:
        # Handle simple numeric values
        if '/' not in value:
            return float(value)

        # Handle mixed numbers (e.g., "1 1/2")
        if ' ' in value:
            whole, fraction_part = value.split(' ', 1)
            num, denom = fraction_part.split('/')
            fraction = Fraction(int(num), int(denom))
            return float(whole) + float(fraction)

        # Handle simple fractions (e.g., "1/2")
        num, denom = value.split('/')
        return float(Fraction(int(num), int(denom)))
    except (ValueError, ZeroDivisionError) as e:
        raise ValueError(f"Invalid fraction format: {value}. Error: {e}")

def format_fraction(value: float) -> str:
    """
    Format a float as a fraction or mixed number string

    Examples:
    - 0.5 -> "1/2"
    - 1.5 -> "1 1/2"
    - 2.0 -> "2"
    """
    if value == int(value):
        return str(int(value))

    # Convert to fraction
    fraction = Fraction(value).limit_denominator(16)

    # If proper fraction (less than 1)
    if fraction < 1:
        return f"{fraction.numerator}/{fraction.denominator}"

    # If improper fraction (greater than or equal to 1)
    whole = int(fraction)
    fraction -= whole

    # If there's a fractional part
    if fraction:
        return f"{whole} {fraction.numerator}/{fraction.denominator}"

    return str(whole)

def scale_quantity(quantity: Union[str, float], factor: float) -> float:
    """Scale a quantity by a factor"""
    qty = quantity if isinstance(quantity, float) else parse_fraction(quantity)
    return qty * factor