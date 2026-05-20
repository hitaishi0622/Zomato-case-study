"""Command-line presentation layer for restaurant recommendations."""

from __future__ import annotations

import logging
import sys

import typer

from restaurant_rec import __version__
from restaurant_rec.application.orchestrator import RecommendationOrchestrator
from restaurant_rec.config.settings import get_settings
from restaurant_rec.domain.filter_results import NoMatchResult
from restaurant_rec.domain.preferences import Budget, UserPreferences
from restaurant_rec.infrastructure import RestaurantRepository
from restaurant_rec.infrastructure.llm import LLMError
from restaurant_rec.services.filter_service import FilterService

app = typer.Typer(
    name="restaurant-rec",
    help="AI-powered restaurant recommendations using dataset filtering and an LLM.",
)


def _safe_text(value: str) -> str:
    return value.encode("ascii", errors="replace").decode("ascii")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stderr,
    )


@app.command("filter")
def filter_preview(
    location: str = typer.Option(..., "--location", "-l", help="City or locality"),
    budget: Budget = typer.Option(..., "--budget", "-b", help="low | medium | high"),
    cuisine: str | None = typer.Option(None, "--cuisine", "-c", help="Cuisine filter"),
    min_rating: float = typer.Option(0.0, "--min-rating", help="Minimum rating (0-5)"),
    limit: int = typer.Option(10, "--limit", help="Max rows to print"),
    refresh_data: bool = typer.Option(False, "--refresh-data", help="Rebuild cache first"),
) -> None:
    """Preview deterministic filtered restaurants without calling the LLM."""
    _configure_logging()
    settings = get_settings()
    repo = RestaurantRepository.from_settings(settings, refresh=refresh_data)
    prefs = UserPreferences(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
    )
    filter_outcome = FilterService(settings=settings).apply(
        repo.dataframe, prefs, available_cities=repo.distinct_cities()
    )

    if isinstance(filter_outcome, NoMatchResult):
        typer.secho("No matches found.", fg=typer.colors.RED)
        for hint in filter_outcome.hints:
            typer.echo(f"  • {hint}")
        raise typer.Exit(code=1)

    typer.secho(
        f"Matched {filter_outcome.total_matched} restaurants; showing top {min(limit, len(filter_outcome.candidates))}.",
        fg=typer.colors.GREEN,
    )
    for index, restaurant in enumerate(filter_outcome.candidates[:limit], start=1):
        cuisines = ", ".join(restaurant.cuisines)
        line = (
            f"{index}. {_safe_text(restaurant.name)} | {_safe_text(cuisines)} | "
            f"{restaurant.rating} stars | Rs {int(restaurant.cost_for_two)} for two | {restaurant.city}"
        )
        typer.echo(line)


@app.command("recommend")
def recommend(
    location: str = typer.Option(..., "--location", "-l", help="City or locality"),
    budget: Budget = typer.Option(..., "--budget", "-b", help="low | medium | high"),
    cuisine: str | None = typer.Option(None, "--cuisine", "-c", help="Cuisine filter"),
    min_rating: float = typer.Option(0.0, "--min-rating", help="Minimum rating (0-5)"),
    extras: str | None = typer.Option(None, "--extras", "-e", help="Free-text preferences"),
    limit: int = typer.Option(5, "--limit", help="Max recommendations to show"),
    refresh_data: bool = typer.Option(False, "--refresh-data", help="Rebuild cache first"),
) -> None:
    """Run full filtering and LLM ranking to show restaurant recommendations."""
    _configure_logging()
    settings = get_settings()
    prefs = UserPreferences(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        extras=extras,
    )

    try:
        orchestrator = RecommendationOrchestrator(settings=settings)
        outcome = orchestrator.recommend(prefs, refresh=refresh_data)
    except LLMError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        typer.echo("Set GROQ_API_KEY or LLM_API_KEY in your .env file.")
        raise typer.Exit(code=1) from exc

    if isinstance(outcome, NoMatchResult):
        typer.secho("No matches found.", fg=typer.colors.RED)
        for hint in outcome.hints:
            typer.echo(f"  • {hint}")
        raise typer.Exit(code=1)

    if outcome.summary:
        typer.secho(_safe_text(outcome.summary), fg=typer.colors.CYAN)

    if outcome.metadata.degraded:
        typer.secho("(Degraded mode: rating-only fallback)", fg=typer.colors.YELLOW)

    for rec in outcome.recommendations[:limit]:
        restaurant = rec.restaurant
        cuisines = ", ".join(restaurant.cuisines)
        typer.secho(f"\n#{rec.rank} {_safe_text(restaurant.name)}", fg=typer.colors.GREEN)
        typer.echo(f"  {restaurant.city} | {restaurant.rating} stars | Rs {int(restaurant.cost_for_two)} for two")
        typer.echo(f"  {_safe_text(rec.explanation)}")

    typer.echo(
        f"\n({len(outcome.recommendations)} recommendations, filter_ms={outcome.metadata.filter_ms:.0f}, llm_ms={outcome.metadata.llm_ms or 0:.0f})"
    )


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    refresh_data: bool = typer.Option(False, "--refresh-data", help="Rebuild cache first"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    _configure_logging()
    settings = get_settings()
    repo = RestaurantRepository.from_settings(settings, refresh=refresh_data)
    typer.echo(f"Restaurant Recommendation System v{__version__}")
    typer.echo(f"Loaded {repo.row_count} restaurants across {len(repo.distinct_cities())} cities.")
    typer.echo(f"Cache: {settings.data_cache_path_resolved}")
    typer.echo("Use 'recommend' or 'filter' commands to run queries.")
