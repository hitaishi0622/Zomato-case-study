"""Tests for Phase 3 LLM layer (prompt, parse, validate, engine)."""

from __future__ import annotations

import json

import pytest

from restaurant_rec.config.settings import Settings
from restaurant_rec.domain.models import Restaurant
from restaurant_rec.domain.preferences import Budget, UserPreferences
from restaurant_rec.infrastructure.llm import LLMError, MockLLMClient
from restaurant_rec.services.prompt_builder import PromptBuilder
from restaurant_rec.services.recommendation_engine import RecommendationEngine
from restaurant_rec.services.response_parser import ResponseParseError, extract_json_text, parse_llm_response
from restaurant_rec.services.validator import RecommendationValidator


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="r_italian",
            name="italian kitchen",
            city="bangalore",
            locality="indiranagar",
            cuisines=["italian", "pizza"],
            rating=4.5,
            cost_for_two=450,
            votes=200,
        ),
        Restaurant(
            id="r_chinese",
            name="dragon wok",
            city="bangalore",
            locality="koramangala",
            cuisines=["chinese"],
            rating=4.0,
            cost_for_two=350,
            votes=150,
        ),
        Restaurant(
            id="r_cafe",
            name="coffee shack",
            city="bangalore",
            cuisines=["cafe", "italian"],
            rating=4.2,
            cost_for_two=400,
            votes=80,
        ),
    ]


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="bangalore",
        budget=Budget.MEDIUM,
        cuisine="italian",
        min_rating=4.0,
        extras="family-friendly",
    )


@pytest.fixture
def mock_response_json() -> dict:
    return {
        "summary": "Great Italian options for families.",
        "recommendations": [
            {
                "id": "r_italian",
                "rank": 1,
                "explanation": "Perfect Italian fit for family-friendly dining.",
            },
            {
                "id": "r_cafe",
                "rank": 2,
                "explanation": "Casual Italian-leaning cafe with good ratings.",
            },
        ],
    }


def test_prompt_includes_all_candidate_ids(
    preferences: UserPreferences, sample_restaurants: list[Restaurant]
) -> None:
    messages = PromptBuilder().build(
        preferences, sample_restaurants, max_recommendations=5
    )
    user_content = messages[1].content
    for r in sample_restaurants:
        assert r.id in user_content
    assert "family-friendly" in user_content


def test_prompt_strict_mode_adds_reminder(preferences: UserPreferences, sample_restaurants: list[Restaurant]) -> None:
    messages = PromptBuilder().build(
        preferences, sample_restaurants, max_recommendations=5, strict=True
    )
    assert "CRITICAL" in messages[0].content


def test_parser_valid_json(mock_response_json: dict) -> None:
    parsed = parse_llm_response(json.dumps(mock_response_json))
    assert parsed.summary is not None
    assert len(parsed.recommendations) == 2


def test_parser_fenced_json(mock_response_json: dict) -> None:
    raw = "```json\n" + json.dumps(mock_response_json) + "\n```"
    assert extract_json_text(raw).startswith("{")
    parsed = parse_llm_response(raw)
    assert parsed.recommendations[0].id == "r_italian"


def test_parser_invalid_json_raises() -> None:
    with pytest.raises(ResponseParseError):
        parse_llm_response("not json at all")


def test_validator_rejects_unknown_id(
    sample_restaurants: list[Restaurant], mock_response_json: dict
) -> None:
    mock_response_json["recommendations"].append(
        {"id": "r_fake", "rank": 3, "explanation": "fake place"}
    )
    parsed = parse_llm_response(json.dumps(mock_response_json))
    result = RecommendationValidator().validate(parsed, sample_restaurants, max_recommendations=5)
    assert result.dropped_invalid_ids == 1
    assert all(r.restaurant.id != "r_fake" for r in result.recommendations)


def test_validator_uses_dataset_facts(
    sample_restaurants: list[Restaurant], mock_response_json: dict
) -> None:
    parsed = parse_llm_response(json.dumps(mock_response_json))
    result = RecommendationValidator().validate(parsed, sample_restaurants, max_recommendations=5)
    top = result.recommendations[0]
    assert top.restaurant.name == "italian kitchen"
    assert top.restaurant.rating == 4.5
    assert top.restaurant.cost_for_two == 450


def test_validator_deduplicates_ids(sample_restaurants: list[Restaurant]) -> None:
    payload = {
        "recommendations": [
            {"id": "r_italian", "rank": 1, "explanation": "a"},
            {"id": "r_italian", "rank": 2, "explanation": "b"},
        ]
    }
    parsed = parse_llm_response(json.dumps(payload))
    result = RecommendationValidator().validate(parsed, sample_restaurants, max_recommendations=5)
    assert result.deduplicated_ids == 1
    assert len(result.recommendations) == 1


def test_mock_llm_end_to_end(
    preferences: UserPreferences,
    sample_restaurants: list[Restaurant],
    mock_response_json: dict,
) -> None:
    mock = MockLLMClient(mock_response_json)
    settings = Settings(llm_provider="groq", max_recommendations=5)
    engine = RecommendationEngine(settings=settings, llm_client=mock)
    result = engine.generate(preferences, sample_restaurants, candidate_count=3)
    assert len(result.recommendations) >= 1
    assert result.metadata.llm_calls == 1
    assert not result.metadata.degraded


def test_validation_retry_then_success(
    preferences: UserPreferences,
    sample_restaurants: list[Restaurant],
) -> None:
    bad = {
        "recommendations": [{"id": "r_fake", "rank": 1, "explanation": "nope"}]
    }
    good = {
        "recommendations": [
            {"id": "r_italian", "rank": 1, "explanation": "Great Italian spot."}
        ]
    }
    call_responses = [bad, good]

    class SequentialMock(MockLLMClient):
        def __init__(self) -> None:
            super().__init__(response_json={})
            self._responses = call_responses

        def complete(self, messages, *, json_mode=True):
            self._call_count += 1
            self.last_messages = messages
            return json.dumps(self._responses[self._call_count - 1])

    mock = SequentialMock()
    engine = RecommendationEngine(settings=Settings(max_recommendations=5), llm_client=mock)
    result = engine.generate(preferences, sample_restaurants)
    assert mock.call_count == 2
    assert len(result.recommendations) == 1


def test_llm_fallback_on_double_failure(
    preferences: UserPreferences,
    sample_restaurants: list[Restaurant],
) -> None:
    mock = MockLLMClient(fail_times=99)
    engine = RecommendationEngine(settings=Settings(max_recommendations=5), llm_client=mock)
    result = engine.generate(preferences, sample_restaurants)
    assert result.metadata.degraded
    assert len(result.recommendations) <= 3
    assert all("unavailable" in r.explanation.lower() or "rating" in r.explanation.lower() for r in result.recommendations)


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    settings = Settings(llm_provider="groq", llm_api_key=None)
    with pytest.raises(LLMError, match="API key"):
        from restaurant_rec.infrastructure.llm.groq_client import resolve_groq_api_key

        resolve_groq_api_key(settings)


def test_parser_partial_without_summary(sample_restaurants: list[Restaurant]) -> None:
    payload = {
        "recommendations": [
            {"id": "r_italian", "rank": 1, "explanation": "Solid choice."}
        ]
    }
    parsed = parse_llm_response(json.dumps(payload))
    assert parsed.summary is None
    result = RecommendationValidator().validate(parsed, sample_restaurants, max_recommendations=5)
    assert len(result.recommendations) == 1
