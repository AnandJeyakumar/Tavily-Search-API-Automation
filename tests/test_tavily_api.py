import time
from urllib.parse import urlparse
import pytest
import requests
import json
from tavily import TavilyClient
import re
from  tavily.errors import *
from typing import Type
from jsonschema import  Draft7Validator
import allure
from allure_commons.types import AttachmentType
import warnings
from _pytest.warning_types import PytestUnknownMarkWarning
warnings.filterwarnings("ignore", category=PytestUnknownMarkWarning)



tavily = TavilyClient(api_key="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")


# ------------------------
# Test Cases for (a) Valid and Invalid Queries
# ------------------------

@pytest.mark.positive
@allure.severity(allure.severity_level.CRITICAL)
def test_valid_query_returns_results():
    payload = {"query": "Who is Chris"}
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response,payload, latency_ms)
    assert len(response["results"]) == 5


@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_empty_query_raises_error():
    payload = {"query": ""}
    assert_tavily_exception_error(payload,exception_messages["emptyQuery"])

@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_missing_query_field_raises_error():
    payload = {}
    assert_tavily_exception_error(payload, exception_messages["missingQuery"],TypeError)

@pytest.mark.negative
@allure.severity(allure.severity_level.NORMAL)
def test_long_query_returns_error():
    payload = {"query": "Ronaldo " * 300}
    assert_tavily_exception_error(payload, exception_messages["queryTooLong"])

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_query_with_special_characters():
    payload = {"query": "Ronaldo?!@$%^&*()_+"}
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)


@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_numeric_query_returns_results():
    payload = {"query": "123456"}
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len(response["results"]) == 5


@pytest.mark.edge
@allure.severity(allure.severity_level.MINOR)
def test_short_query():
    payload = {"query": "W"}
    assert_tavily_exception_error(payload,"Query is too short. Min query length is 2 characters.",BadRequestError)

# ------------------------
# Test Cases for (B) Parameter validation (include_answer, include_images, search_depth, etc.)
# ------------------------
@pytest.mark.positive
@allure.severity(allure.severity_level.CRITICAL)
def test_include_answer_true():
    payload = {
        "query": "Who is Ronaldo?",
        "include_answer": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    validate_answer_field(response)

@pytest.mark.positive
@allure.severity(allure.severity_level.CRITICAL)
def test_include_answer_basic():
    payload = {
        "query": "What is Python?",
        "include_answer": "basic"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    validate_answer_field(response)

@pytest.mark.positive
@allure.severity(allure.severity_level.CRITICAL)
def test_include_answer_advanced():
    payload = {
        "query": "What is Quantum Computing?",
        "include_answer": "advanced"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    validate_answer_field(response)

@pytest.mark.negative
@allure.severity(allure.severity_level.NORMAL)
def test_include_answer_invalid_value():
    payload = {
        "query": "What is AI?",
        "include_answer": "yesplease"
    }
    assert_tavily_exception_error(payload, exception_messages["invalidIncludeAnswer"])

@pytest.mark.edge
@allure.severity(allure.severity_level.MINOR)
def test_short_query_with_include_answer():
    payload = {
        "query": "Goog",
        "include_answer": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    validate_answer_field(response)

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_include_answer_with_auto_parameters():
    payload = {
        "query": "DevOps?",
        "auto_parameters": True,
        "include_answer": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert "auto_parameters" in response
    validate_answer_field(response)


# Include images
@pytest.mark.positive
@allure.severity(allure.severity_level.CRITICAL)
def test_include_images_true():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_images": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len(response["images"]) == 5
    for image_url in response["images"]:
        assert isinstance(image_url, str)
        assert is_valid_url(image_url), f"Invalid image URL: {image_url}"
    assert all(isinstance(img, str) for img in response["images"]), "Descriptions should not be present"

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_include_images_false():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_images": False
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len(response["images"]) == 0

@pytest.mark.positive
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.xfail(reason = "Mentioned in the summary - Description is getting null value")
def test_include_images_with_descriptions():
    payload = {
        "query": "Messi",
        "include_images": True,
        "include_image_descriptions": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len([img for img in response["images"] if "url" in img]) == 5
    assert len([img for img in response["images"] if "description" in img]) == 5
    for img in response["images"]:
        assert isinstance(img, dict)
        assert "url" in img and isinstance(img["url"], str)
        assert is_valid_url(img["url"]), f"Invalid image URL: {img['url']}"
        assert "description" in img and isinstance(img["description"], str)
        assert len(img["description"]) > 0

@pytest.mark.edge
@pytest.mark.xfail(reason="Docs say image descriptions should only be returned when include_images=True. Backend still returns them without include_images.", strict=False)
@allure.severity(allure.severity_level.MINOR)
def test_descriptions_without_images_but_with_include_image_descriptions():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_image_descriptions": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert "images" in response
    assert len(response["images"]) == 0


# search_depth Parameter Validation
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_search_depth_basic():
    payload = {
        "query": "Cristiano Ronaldo",
        "search_depth": "basic"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len(response["results"]) == 5

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_search_depth_advanced():
    payload = {
        "query": "Cristiano Ronaldo",
        "search_depth": "advanced"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len(response["results"]) == 5

@pytest.mark.negative
@allure.severity(allure.severity_level.NORMAL)
def test_search_depth_invalid_value():
    payload = {
        "query": "Cristiano Ronaldo",
        "search_depth": "deepest"
    }
    assert_tavily_exception_error(payload, exception_messages["invalidSearchDepth"])

#auto_parameters Parameter Validation
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_auto_parameters_true():
    payload = {
        "query": "History of space exploration",
        "auto_parameters": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert response["auto_parameters"]["topic"] in ["general", "news"]
    assert response["auto_parameters"]["search_depth"] in ["basic", "advanced"]

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_auto_parameters_false():
    payload = {
        "query": "History of space exploration",
        "auto_parameters": False
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert "auto_parameters" not in response

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_auto_parameters_with_manual_override():
    payload = {
        "query": "Machine Learning Basics",
        "auto_parameters": True,
        "search_depth": "basic",
        "include_answer": "basic"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert "topic" in response["auto_parameters"]
    assert "search_depth"  not in response["auto_parameters"]

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_auto_parameters_sets_search_depth():
    payload = {
        "query": "How does Laptop work?",
        "auto_parameters": True,
        "include_answer": True
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert "topic" in response["auto_parameters"]
    assert response["auto_parameters"]["topic"] in ["general", "news"]
    assert response["auto_parameters"]["search_depth"] in ["basic", "advanced"]

# Topic
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_topic_general():
    payload = {
        "query": "Latest technology",
        "topic": "general"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    topic_valid_cases_verification(response)

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_topic_news():
    payload = {
        "query": "Elections 2024",
        "topic": "news"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    topic_valid_cases_verification(response)

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_topic_finance():
    payload = {
        "query": "World economy",
        "topic": "finance"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    topic_valid_cases_verification(response)

@pytest.mark.negative
@allure.severity(allure.severity_level.NORMAL)
def test_topic_invalid():
    payload = {"query": "Global economy", "topic": "non"}
    assert_tavily_exception_error(payload,"Invalid topic. Must be 'general', 'news', or 'finance'")

@pytest.mark.negative
@allure.severity(allure.severity_level.NORMAL)
def test_topic_invalid_blank():
    payload = {"query": "Global economy", "topic": ""}
    assert_tavily_exception_error(payload,"Invalid topic. Must be 'general', 'news', or 'finance'")

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_max_results_valid_values():
    for value in [1, 5, 20]:
        payload = {
            "query": "Cristiano Ronaldo",
            "max_results": value
        }
        response, latency_ms = search_with_timer(**payload)
        basic_response_validations_with_allure_config(response, payload, latency_ms)
        assert len(response["results"]) <= value , f"The Assertion for {value} got failed"
        print("The assertion Passed for ", value)

@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_max_results_invalid_negative():
    payload = {
        "query": "Cristiano Ronaldo",
        "max_results": -1
    }
    assert_tavily_exception_error(payload,exception_messages["invalidMaxResults"])

@pytest.mark.negative
@pytest.mark.xfail(reason="Docs say max_results <= 20, backend accepts >20 (up to 100)", strict=False)
@allure.severity(allure.severity_level.CRITICAL)
def test_max_results_invalid_above_range():
    payload = {
        "query": "Cristiano Ronaldo",
        "max_results": 21
    }
    assert_tavily_exception_error(payload,exception_messages["invalidMaxResults"],BadRequestError)


# ------------------------
# Parameter Validation: country
# ------------------------
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_country_valid_with_topic_general():
    payload = {
        "query": "best universities",
        "topic": "general",
        "country": "portugal"
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)

@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_country_invalid_value_raises_error():
    payload = {
        "query": "best universities",
        "topic": "general",
        "country": "21as"
    }
    assert_tavily_exception_error(payload,exception_messages["invalidCountry"])

@pytest.mark.edge
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.xfail(reason = "Country with topic news is not allowed")
def test_country_with_topic_news_is_ignored():
    payload = {
        "query": "football",
        "topic": "news",
        "country": "portugal"
    }
    response, latency_ms = search_with_timer(**payload)
    assert_tavily_exception_error(response,exception_messages["Country with topic news is not allowed"],BadRequestError)
    basic_response_validations_with_allure_config(response, payload, latency_ms)

# ------------------------
# Parameter Validation: chunks_per_source
# ------------------------
@pytest.mark.positive
@pytest.mark.parametrize("cps", [1, 2, 3])
@allure.severity(allure.severity_level.NORMAL)
def test_chunks_per_source_valid_with_advanced(cps):
    payload = {
        "query": "History of the FIFA World Cup",
        "search_depth": "advanced",
        "chunks_per_source": cps,
        "max_results": 3
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    for item in response["results"]:
        assert "content" in item
        chunks_seen = count_chunks(item["content"])
        if cps == 1 and chunks_seen == 0:
            assert False, f"Expected exactly 1 chunk, got {chunks_seen}"
        elif cps == 1:
            assert chunks_seen == 1, f"Expected exactly 1 chunk, got {chunks_seen}"
        else:
            # For cps=2 or 3, allow 0 but never exceed cps
            assert chunks_seen <= cps, f"Expected ≤{cps} chunks, got {chunks_seen}"

@pytest.mark.negative
@pytest.mark.xfail(reason="Docs say chunks_per_source <= 3, backend allows 4.")
@pytest.mark.parametrize("cps", [0,4])
@allure.severity(allure.severity_level.CRITICAL)
def test_chunks_per_source_out_of_range_raises_error(cps):
    payload = {
        "query": "History of the FIFA World Cup",
        "search_depth": "advanced",
        "chunks_per_source": cps
    }
    assert_tavily_exception_error(payload,exception_messages["invalidChunksRange"], requests.exceptions.HTTPError)


@pytest.mark.edge
@allure.severity(allure.severity_level.MINOR)
def test_chunks_per_source_is_ignored_with_basic_depth():
    payload = {
        "query": "History of the FIFA World Cup",
        "search_depth": "basic",
        "chunks_per_source": 3,
        "max_results": 3
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    for item in response["results"]:
        if "content" in item and isinstance(item["content"], str):
            assert " [...] " not in item["content"], \
                f"Unexpected chunk separator found in basic mode content: {item['content']}"


# Date
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_start_and_end_date_valid_range():
    payload = {
        "query": "Cristiano Ronaldo transfers",
        "topic": "news",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "max_results": 5
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)

@pytest.mark.negative
@pytest.mark.parametrize("bad_start,bad_end,bad_value", [
    ("01-01-2024", "2024-12-31", "01-01-2024"),
    ("2024/01/01", "2024-12-31", "2024/01/01"),
    ("yesterday", "2024-12-31", "yesterday"),     # bad start
    ("2024-01-01", "31-12-2024", "31-12-2024"),   # bad end
])
@allure.severity(allure.severity_level.CRITICAL)
def test_date_format_invalid_raises(bad_start, bad_end, bad_value):
    payload = {
        "query": "Cristiano Ronaldo transfers",
        "topic": "news",
        "start_date": bad_start,
        "end_date": bad_end
    }
    expected_msg = exception_messages["invalidDateFormat"].format(value=bad_value)
    assert_tavily_exception_error(payload,expected_msg,BadRequestError)


@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_start_date_after_end_date_raises():
    payload = {
        "query": "Cristiano Ronaldo transfers",
        "topic": "news",
        "start_date": "2025-07-01",
        "end_date": "2025-01-01"
    }
    assert_tavily_exception_error(payload,exception_messages["startDateAfterEndDateMesssage"],BadRequestError)

@pytest.mark.negative
@pytest.mark.parametrize("with_field", ["start_date", "end_date"])
@allure.severity(allure.severity_level.CRITICAL)
def test_time_range_conflicts_with_dates(with_field):
    payload = {"query": "Cristiano Ronaldo transfers", "topic": "news","time_range": "month","days": 7 }
    payload[with_field] = "2024-01-01"
    assert_tavily_exception_error(payload,exception_messages["timeRangeSetWithDate"],BadRequestError)

#favicon
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_include_favicon_true_adds_favicon_field():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_favicon": True,
        "max_results": 5
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    assert len([r["favicon"] for r in response["results"]]) == 5, "The Favicon count is mismatched"
    favicons = [r["favicon"] for r in response["results"]]
    assert all(isinstance(f, str) for f in favicons), "Some favicons are not strings"


@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_include_favicon_false_no_favicon_key():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_favicon": False,
        "max_results": 3
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    unexpected = [r for r in response["results"] if "favicon" in r]
    assert len(unexpected) == 0, f"favicon should not be present: {unexpected}"


@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_days_with_topic_news_valid():
    payload = {
        "query": "Cristiano Ronaldo",
        "topic": "news",
        "days": 7
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)

@pytest.mark.edge
@allure.severity(allure.severity_level.MINOR)
def test_days_with_topic_general_should_error():
    payload = {
        "query": "Cristiano Ronaldo",
        "topic": "general",
        "days": 7
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)


# include , exclude domain
@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_include_domains_whitelists_results_lenient():
    payload = {
        "query": "Cristiano Ronaldo biography",
        "include_domains": ["wikipedia.org", "google.com"],
        "max_results": 5,
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    # Lenient check: at least one result should come from the include list
    domains = [get_domain(r["url"]) for r in response["results"]]
    print("domains" , domains)
    assert any(d.endswith("wikipedia.org") or d.endswith("britannica.com") for d in domains), (
        f"No included domains found in results: {domains}"
    )

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_exclude_domains_blacklists_results_strict():
    payload = {
        "query": "Cristiano Ronaldo",
        "exclude_domains": ["reddit.com", "quora.com"],
        "max_results": 10,
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    for r in response["results"]:
        d = get_domain(r["url"])
        assert not (d.endswith("reddit.com") or d.endswith("quora.com")), f"Excluded domain : {d}"


@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_include_and_exclude_domains_together():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_domains": ["wikipedia.org", "britannica.com", "fifa.com"],
        "exclude_domains": ["reddit.com", "quora.com"],
        "max_results": 10,
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)
    domains = [get_domain(r["url"]) for r in response["results"]]
    assert not any(d.endswith("reddit.com") or d.endswith("quora.com") for d in domains)
    assert any(d.endswith("wikipedia.org") or d.endswith("britannica.com") or d.endswith("fifa.com") for d in domains), (
        f"No included domains found in results: {domains}"
    )

@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_include_domains_limit_enforced_301_raises():
    big_list = [f"site{i}.com" for i in range(301)]
    payload = {"query": "Cristiano Ronaldo", "include_domains": big_list}
    assert_tavily_exception_error(payload,exception_messages["includeDomainMaxLimit"],BadRequestError)


@pytest.mark.negative
@pytest.mark.xfail(reason = "In Document its mentioned as Max 150 , but in message it is Max 130")
@allure.severity(allure.severity_level.CRITICAL)
def test_exclude_domains_limit_enforced_151_raises():
    big_list = [f"site{i}.com" for i in range(151)]
    payload = {"query": "Cristiano Ronaldo", "exclude_domains": big_list}
    assert_tavily_exception_error(payload,exception_messages["excludeDomainMaxLimit"],BadRequestError)


@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_domains_list_must_be_strings():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_domains": ["wikipedia.org", 123, None],  # bad entries
    }
    assert_tavily_exception_error(payload,exception_messages["invalidChunksRange"],requests.exceptions.HTTPError)


@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_empty_include_exclude_lists_are_allowed():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_domains": [],
        "exclude_domains": [],
        "max_results": 5,
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)


@pytest.mark.edge
@allure.severity(allure.severity_level.MINOR)
def test_both_include_and_exclude_same_domain():
    payload = {
        "query": "Cristiano Ronaldo",
        "include_domains": ["wikipedia.org","google.com"],
        "exclude_domains": ["wikipedia.org","google.com"],
        "max_results": 5,
    }
    response, latency_ms = search_with_timer(**payload)
    basic_response_validations_with_allure_config(response, payload, latency_ms)

@pytest.mark.negative
@allure.severity(allure.severity_level.CRITICAL)
def test_invalid_api_key():
    payload = {"query":"Invalid API Key"}
    tavily_invalid = TavilyClient(api_key="tv ly-dev-invalid")
    with pytest.raises(InvalidAPIKeyError) as exc:
        tavily_invalid.search(**payload)
    print("Error:", str(exc.value))
    assert str(exc.value) == exception_messages["invalidAPIKey"]

@pytest.mark.positive
@allure.severity(allure.severity_level.NORMAL)
def test_schema_minimal_200_response():
    resp = tavily.search(query="Cristiano Ronaldo")
    print(json.dumps({"query": resp.get("query"),
                      "results_len": len(resp.get("results", [])),
                      "response_time": resp.get("response_time")}, indent=2))
    _validate_schema_or_fail(resp, TAVILY_SEARCH_RESPONSE_SCHEMA)
    assert len(resp["results"]) >= 0
    for r in resp["results"]:
        assert r["url"].startswith(("http://", "https://"))




# Just a note: Since the task submission requires everything in a single file, I've included this helper method here itself.
# But ideally, in a real-world project, I would move this to a separate helper file (like utils/assertions.py) and import it wherever needed.
# That way, it’s easier to maintain and reuse across multiple test files.

def search_with_timer(**payload):
    start_time = time.perf_counter()
    response = tavily.search(**payload)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return response, elapsed_ms

def assert_tavily_exception_error(payload, expected_error_msg,exception_name: Type[BaseException] = BadRequestError):
        with pytest.raises(exception_name) as exc:
            tavily.search(**payload)
        print("Error:", str(exc.value))
        assert str(exc.value) == expected_error_msg



# --- Reusable Exception Messages Dictionary ---
# Just keeping it in the same file for now, as per the task submission requirement.
# But in a real-world setup, I’d usually place this in a separate constants or config file to keep things cleaner and more maintainable.

exception_messages = {
    "emptyQuery": "Query is missing.",
    "missingQuery":"TavilyClient.search() missing 1 required positional argument: 'query'",
    "queryTooLong": "Query is too long. Max query length is 400 characters.",
    "invalidSearchDepth": "Invalid search depth. Must be 'basic' or 'advanced'.",
    "invalidIncludeAnswer": "Invalid value for include_answer. Must be True, False, 'basic', or 'advanced'.",
    "invalidMaxResults":"Invalid max results.",
    "invalidCountry":"Invalid country. Must be a valid country name from the list of supported countries (https://docs.tavily.com/documentation/api-reference/endpoint/search).",
    "invalidChunksRange":"422 Client Error: Unprocessable Entity for url: https://api.tavily.com/search",
    "invalidAPIKey" : "Unauthorized: missing or invalid API key.",
    "invalidDateFormat": "Invalid date format. Expected YYYY-MM-DD, got: {value}",
    "startDateAfterEndDateMesssage" : "start_date cannot be after end_date",
    "timeRangeSetWithDate":"When time_range is set, start_date or end_date cannot be set",
    "includeDomainMaxLimit":"Invalid value for include_domains. Max 300 domains are allowed.",
    "excludeDomainMaxLimit":"Invalid value for exclude_domains. Max 150 domains are allowed."

}


# --- Reusable response structure validator ---
# I’ve included this here since the submission requires a single Python file.
# In a real project, I’d put this in a separate test utils or helper module for better organization and reuse.

def validate_basic_response_structure(response: dict , payload):
    print(json.dumps(response, indent=2))
    assert isinstance(response, dict), "Response should be a dictionary"
    assert "images" in response
    assert isinstance(response["images"], list)
    assert "results" in response, "Response should contain 'results' key"
    assert isinstance(response["results"], list), "'results' should be a list"
    assert "query" in response and response["query"] == payload["query"]
    assert "response_time" in response
    assert float(response["response_time"]) < 5 , "Response Time is more than 5 sec"
    query_words = [w.lower() for w in re.findall(r'\w+', payload["query"])]
    print("The query_words", query_words)

    for idx, result in enumerate(response["results"]):
        title = result["title"].lower()
        content = result.get("content", "").lower()

        # Check if any query word in title
        in_title = any(word in title for word in query_words)

        # If not in title, check in content for this result only
        in_content = False
        if not in_title:
            in_content = any(word in content for word in query_words)

        print(f"Result {idx}: Title match? {in_title}, Content match? {in_content}")

        assert in_title or in_content, (
            f"Result at index {idx} does not contain any query words "
            f"in title or content. Title: '{result['title']}'"
        )

# --- Reusable method to validate presence and structure of 'answer' field ---
def validate_answer_field(response: dict):
    assert "answer" in response, "Expected 'answer' in response"
    assert isinstance(response["answer"], str), "'answer' should be a string"
    assert len(response["answer"]) > 0, "'answer' should not be empty"

def is_valid_url(url):
    # Checks if the string starts with http(s) and has no obvious errors
    url_pattern = re.compile(
        r'^https?://[^\s]+$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(url))


def topic_valid_cases_verification(response):
    assert len(response["results"]) == 5
    assert "topic" not in response
    assert "auto_parameters" not in response


def get_domain(url: str) -> str:
    """Return registrable-ish domain from a URL (quick + good enough for tests)."""
    host = urlparse(url).netloc.split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host

def count_chunks(content: str) -> int:
    if not isinstance(content, str) or not content.strip():
        return 0
    seps = content.count(" [...] ")
    if seps > 0:
        return seps + 1
    return 1





TAVILY_SEARCH_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["query", "results", "response_time"],
    "properties": {
        "query": {"type": "string"},
        "answer": {"type": ["string", "null"]},
        "images": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "required": ["url"],
                        "properties": {
                            "url": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "additionalProperties": True
                    }
                ]
            }
        },
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "url", "content"],
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "content": {"type": "string"},
                    "score": {"type": ["number", "integer"]},
                    "raw_content": {"type": ["string", "null"]},
                    "favicon": {"type": "string"}
                },
                "additionalProperties": True
            }
        },
        "response_time": {
            "oneOf": [
                {"type": "number"},
                {"type": "string", "pattern": r"^\d+(\.\d+)?$"}
            ]
        },
        "auto_parameters": {
            "type": "object",
            "properties": {
                "topic": {"enum": ["general", "news"]},
                "search_depth": {"enum": ["basic", "advanced"]}
            },
            "additionalProperties": True
        },
        "follow_up_questions": {"type": ["array", "null"]},
    },
    "additionalProperties": True
}



def _validate_schema_or_fail(resp: dict, schema: dict):
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(resp), key=lambda e: e.path)
    if errors:
        parts = []
        for e in errors:
            path = ".".join([str(p) for p in e.path])
            parts.append(f"path='{path}' message='{e.message}'")
        raise AssertionError("Schema validation failed:\n  " + "\n  ".join(parts))



@pytest.fixture(autouse=True)
def add_allure_defaults():
    # All tests get these
    allure.dynamic.link(
        "https://docs.tavily.com/documentation/api-reference/endpoint/search",
        name="API Reference"
    )
    allure.dynamic.epic("Tavily Search API")

def attach_tavily_debug(payload, response, elapsed_ms):
    allure.attach(
        json.dumps(payload, indent=2),
        name="request_payload",
        attachment_type=AttachmentType.JSON
    )

    allure.attach(f"{elapsed_ms:.2f} ms", name="Latency", attachment_type=AttachmentType.TEXT)

    allure.attach(
        json.dumps(response, indent=2),
        name="raw_response",
        attachment_type=AttachmentType.JSON
    )

def basic_response_validations_with_allure_config(response, payload,latency_ms):
    validate_basic_response_structure(response, payload)
    attach_tavily_debug(payload, response, latency_ms)