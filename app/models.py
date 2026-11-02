from dataclasses import dataclass


@dataclass
class Ingredient:
    id: int = None
    name: str = ""
    vendor: str = ""
    purchase_volume: float = 0.0
    volume_unit: str = ""
    total_grams: float = 0.0
    purchase_price: float = 0.0
    created_at: str = ""


@dataclass
class Packaging:
    id: int = None
    name: str = ""
    supplier: str = ""
    purchase_volume: int = 0
    purchase_price: float = 0.0
    moq_for_price: int = 0
    created_at: str = ""


@dataclass
class Formula:
    id: int = None
    name: str = ""
    grams_per_unit: float = 0.0
    notes: str = ""
    created_at: str = ""


@dataclass
class FormulaIngredient:
    id: int = None
    formula_id: int = None
    ingredient_id: int = None
    percent: float = 0.0


@dataclass
class Product:
    id: int = None
    slug: str = ""
    name: str = ""
    description: str = ""
    photo: str = ""
    formula_id: int = None
    category: str = ""
    created_at: str = ""


@dataclass
class Post:
    id: int = None
    slug: str = ""
    title: str = ""
    body: str = ""
    created_at: str = ""


@dataclass
class ContactMessage:
    id: int = None
    name: str = ""
    email: str = ""
    message: str = ""
    created_at: str = ""
