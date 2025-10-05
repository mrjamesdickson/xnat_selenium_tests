from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from xnat_selenium.element_specifications import (
    Element,
    ElementSpecifications,
    EqualityElementComparator,
    Locator,
    MaxPercentToleranceElementComparator,
    TextIndexArray,
)


def compose_specifications() -> ElementSpecifications:
    return ElementSpecifications(
        comparators=(
            EqualityElementComparator(
                (
                    Element(Locator("xpath", "//my/div[3]"), "happy"),
                    Element(Locator("xpath", "//my/div[4]"), Decimal("3.00")),
                    Element(Locator("xpath", "//my/div[5]"), "cat"),
                    Element(Locator("id", "summary"), "passed"),
                )
            ),
            MaxPercentToleranceElementComparator(
                Decimal("1.0"),
                (
                    Element(
                        Locator(
                            "xpath",
                            "$summary_tbody/tr[$indexCache(Left-Pallidum)]/td[2]",
                        ),
                        Decimal("100000.0"),
                    ),
                ),
            ),
        ),
        locator_caches=(
            TextIndexArray(
                id="indexCache",
                locator="//span[@id='full_summary']//tbody/tr/td[1]",
                offset=2,
            ),
        ),
        locator_replacements={
            "$summary_tbody": "//span[@id='full_summary']//tbody"
        },
    )


def test_deserialize_sample_file():
    payload = Path("tests/resources/sample_element_specifications.yaml").read_text()
    assert ElementSpecifications.from_yaml(payload) == compose_specifications()


def test_serialize_matches_sample_output():
    expected = Path(
        "tests/resources/sample_element_specifications_serialized.yaml"
    ).read_text()
    assert compose_specifications().to_yaml() == expected


def test_round_trip_preserves_payload():
    spec = compose_specifications()
    assert ElementSpecifications.from_yaml(spec.to_yaml()) == spec

