"""Streamlit UI for the restaurant recommendation system."""

from __future__ import annotations

import streamlit as st

from restaurant_rec.application.orchestrator import RecommendationOrchestrator
from restaurant_rec.config.settings import get_settings
from restaurant_rec.domain.filter_results import NoMatchResult
from restaurant_rec.domain.preferences import Budget, UserPreferences
from restaurant_rec.infrastructure import RestaurantRepository
from restaurant_rec.infrastructure.llm.base import LLMError
from restaurant_rec.services.filter_service import FilterService


def load_settings() -> object:
    return get_settings()


def load_repository(settings, refresh: bool = False) -> RestaurantRepository:
    return RestaurantRepository.from_settings(settings, refresh=refresh)


def main() -> None:
    st.set_page_config(
        page_title="Restaurant Recommender",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    settings = load_settings()
    st.sidebar.title("Restaurant Recommender")
    st.sidebar.markdown(
        "Use this app to filter restaurants and generate AI-backed recommendations."
    )
    st.sidebar.markdown("---")

    refresh_cache = st.sidebar.button("Refresh dataset cache")
    cache_path = settings.data_cache_path_resolved
    st.sidebar.write("**Cache path:**")
    st.sidebar.code(str(cache_path))
    st.sidebar.write("**LLM provider:**")
    st.sidebar.text(settings.llm_provider)

    location = st.sidebar.text_input("Location or locality", value="bangalore")
    budget = st.sidebar.selectbox(
        "Budget tier", [budget.value for budget in Budget], index=1
    )
    cuisine = st.sidebar.text_input("Cuisine", value="italian")
    min_rating = st.sidebar.slider("Minimum rating", min_value=0.0, max_value=5.0, value=4.0, step=0.5)
    extras = st.sidebar.text_input("Extras / preferences", value="family-friendly")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Actions")
    run_filter = st.sidebar.button("Preview filter")
    run_recommend = st.sidebar.button("Run recommendation")

    if refresh_cache:
        with st.spinner("Refreshing dataset cache..."):
            load_repository(settings, refresh=True)
        st.success("Dataset cache refreshed.")

    if run_filter or run_recommend:
        with st.spinner("Loading dataset..."):
            repo = load_repository(settings)

        if not repo.row_count:
            st.error("No restaurants available in the local cache. Refresh the dataset.")
            return

        preferences = UserPreferences(
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating,
            extras=extras,
        )

        if run_filter:
            filter_service = FilterService(settings=settings)
            outcome = filter_service.apply(
                repo.dataframe, preferences, available_cities=repo.distinct_cities()
            )
            if isinstance(outcome, NoMatchResult):
                st.warning("No restaurants matched your filters.")
                for hint in outcome.hints:
                    st.write(f"- {hint}")
                return

            st.success(f"Matched {outcome.total_matched} restaurants. Showing top {len(outcome.candidates)}.")
            st.write("### Top filter candidates")
            for restaurant in outcome.candidates:
                cuisines = ", ".join(restaurant.cuisines)
                st.write(f"**{restaurant.name}** — {restaurant.city}")
                st.write(f"Rating: {restaurant.rating} | Cost for two: Rs {int(restaurant.cost_for_two)} | {cuisines}")
                st.write("---")
            return

        if run_recommend:
            try:
                orchestrator = RecommendationOrchestrator(settings=settings)
            except LLMError as e:
                st.error(
                    f"⚠️ **API Key Not Configured**\n\n"
                    f"To use recommendations, you need to add your Groq API key:\n\n"
                    f"1. Get a free API key at https://console.groq.com/keys\n"
                    f"2. In Streamlit Cloud: Click ⋯ → Settings → Secrets\n"
                    f"3. Add this line:\n"
                    f"```\n"
                    f"GROQ_API_KEY = \"your-key-here\"\n"
                    f"```\n"
                    f"4. Save and refresh the app\n\n"
                    f"**Note:** Filter preview (left) works without an API key!"
                )
                return
            
            with st.spinner("Generating recommendations..."):
                outcome = orchestrator.recommend(preferences)

            if isinstance(outcome, NoMatchResult):
                st.warning("No restaurants matched your filters.")
                for hint in outcome.hints:
                    st.write(f"- {hint}")
                return

            if outcome.summary:
                st.info(outcome.summary)

            if outcome.metadata.degraded:
                st.warning("Degraded mode: showing top-rated fallback recommendations.")

            st.write("### Recommendations")
            for rec in outcome.recommendations:
                restaurant = rec.restaurant
                cuisines = ", ".join(restaurant.cuisines)
                st.markdown(f"#### {rec.rank}. {restaurant.name}")
                st.write(f"**Location:** {restaurant.city}")
                st.write(f"**Rating:** {restaurant.rating} | **Cost for two:** Rs {int(restaurant.cost_for_two)}")
                st.write(f"**Cuisines:** {cuisines}")
                st.write(f"**Explanation:** {rec.explanation}")
                st.write("---")

            st.sidebar.markdown("### Performance")
            st.sidebar.write(f"Filter time: {outcome.metadata.filter_ms:.0f} ms")
            st.sidebar.write(f"LLM time: {outcome.metadata.llm_ms:.0f} ms")
            st.sidebar.write(f"LLM calls: {outcome.metadata.llm_calls}")


if __name__ == "__main__":
    main()
