from pydantic import BaseModel, validator
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum
from fractions import Fraction


class Genre(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    APPETIZER = "appetizer"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    EGG_FREE = "egg_free"


class MeasuringUnit(str, Enum):
    CUP = "cup"
    CUPS = "cups"
    TABLESPOON = "tablespoon"
    TABLESPOONS = "tablespoons"
    TEASPOON = "teaspoon"
    TEASPOONS = "teaspoons"
    OUNCE = "ounce"
    OUNCES = "ounces"
    POUND = "pound"
    POUNDS = "pounds"
    GRAM = "gram"
    GRAMS = "grams"
    KILOGRAM = "kilogram"
    KILOGRAMS = "kilograms"
    LITER = "liter"
    LITERS = "liters"
    MILLILITER = "milliliter"
    MILLILITERS = "milliliters"
    PIECE = "piece"
    PIECES = "pieces"
    WHOLE = "whole"
    PINCH = "pinch"
    DASH = "dash"


class Ingredient(BaseModel):
    name: str
    quantity: Union[float, str]  # Accept both float and string (for fractions)
    unit: MeasuringUnit

    @validator('quantity')
    def validate_quantity(cls, v):
        if isinstance(v, float):
            return v

        if isinstance(v, str):
            try:
                if '/' in v:
                    # Simple fraction
                    if ' ' not in v:
                        num, denom = v.split('/')
                        return float(Fraction(int(num.strip()), int(denom.strip())))
                    # Mixed number
                    else:
                        whole, frac = v.split(' ', 1)
                        num, denom = frac.split('/')
                        return float(int(whole.strip())) + float(Fraction(int(num.strip()), int(denom.strip())))
                # Plain decimal or integer
                return float(v)
            except (ValueError, ZeroDivisionError):
                raise ValueError(
                    f"Invalid quantity format: {v}. Use a number, fraction (e.g., '1/2'), or mixed number (e.g., '1 1/2')")

        return v

    def dict(self, *args, **kwargs):
        """Override dict to ensure quantity is stored as a float"""
        d = super().dict(*args, **kwargs)

        # Convert quantity to float if it's a string
        if isinstance(d["quantity"], str):
            d["quantity"] = self.validate_quantity(d["quantity"])

        return d


class Recipe(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    prep_time: Optional[int] = 0  # Add prep time field in minutes
    cook_time: Optional[int] = 0  # Add cook time field in minutes
    created_by: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class RecipeCreate(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    prep_time: Optional[int] = 0  # Add prep time field
    cook_time: Optional[int] = 0  # Add cook time field


class RecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    serving_size: Optional[int] = None
    genre: Optional[Genre] = None
    prep_time: Optional[int] = None  # Add prep time field
    cook_time: Optional[int] = None  # Add cook time field


class RecipeResponse(BaseModel):
    id: str
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    prep_time: Optional[int] = 0  # Add prep time field
    cook_time: Optional[int] = 0  # Add cook time field
    created_by: str
    created_at: datetime
