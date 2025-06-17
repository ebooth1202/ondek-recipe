from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Genre(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    APPETIZER = "appetizer"

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
    quantity: float
    unit: MeasuringUnit

class Recipe(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    created_by: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class RecipeCreate(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre

class RecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    serving_size: Optional[int] = None
    genre: Optional[Genre] = None

class RecipeResponse(BaseModel):
    id: str
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    created_by: str
    created_at: datetime