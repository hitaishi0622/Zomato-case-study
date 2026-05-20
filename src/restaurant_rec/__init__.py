"""AI-powered restaurant recommendation system."""

__version__ = "0.1.0"

from restaurant_rec.config import Settings, get_settings
from restaurant_rec.domain import Restaurant
from restaurant_rec.domain import FilterResult, NoMatchResult, UserPreferences
from restaurant_rec.infrastructure import RestaurantRepository
from restaurant_rec.services import FilterService, RecommendationEngine

__all__ = [
    "__version__",
    "Settings",
    "get_settings",
    "Restaurant",
    "RestaurantRepository",
    "UserPreferences",
    "FilterResult",
    "NoMatchResult",
    "FilterService",
    "RecommendationEngine",
]
