"""Security priorities retain unknown coverage and never export alert content."""
import json

import pytest

from laurea.security import summarize_alerts


def alert(number=1, **fields):
    return {"number": number, "state": "open", **fields}


def test_vulnerability_severities_are_observed_not_inferred():
    result = summarize_alerts([
        alert(1, security_vulnerability={"severity": "critical", "package": {"name": "PRIVATE"}}),
        alert(2, security_vulnerability={"severity": "high"}),
        alert(3, security_vulnerability={"severity": "low"}),
        alert(4, security_advisory={"severity": "high"}),
        alert(5, security_vulnerability={"severity": ["high"]}),
    ], "dependabot")
    assert result["severity_counts_observed"] == {
        "critical": 1, "high": 1, "medium": 0, "low": 1, "unmeasured": 2}
    assert result["open_alerts_observed"] == 5
    assert result["severity_status"] == "unmeasured"
    assert "PRIVATE" not in json.dumps(result)


def test_code_scanning_warning_is_not_a_security_severity():
    result = summarize_alerts([
        alert(1, rule={"severity": "warning", "security_severity_level": "high"}),
        alert(2, rule={"severity": "error"}),
    ], "code_scanning")
    assert result["severity_counts_observed"]["high"] == 1
    assert result["severity_counts_observed"]["unmeasured"] == 1


def test_credentials_remain_an_explicit_obligation_without_secret_content():
    result = summarize_alerts([alert(secret="PRIVATE", locations_url="PRIVATE",  # allow-secret: synthetic redaction sentinel, not a credential
                                    metadata=[{"value": "PRIVATE"}])], "secret_scanning")
    assert result["credential_alerts_observed"] == 1
    assert "severity_counts_observed" not in result
    assert "PRIVATE" not in json.dumps(result)
    assert result["coverage"] == "unmeasured"


@pytest.mark.parametrize("source", ["dependabot", "code_scanning", "secret_scanning"])
def test_empty_list_is_not_enabled_coverage(source):
    result = summarize_alerts([], source)
    assert result["open_alerts_observed"] == 0
    assert result["status"] == "measured"
    assert result["coverage"] == "unmeasured"


def test_full_page_preserves_observed_high_alerts_and_unknown_remainder():
    result = summarize_alerts([alert(n, security_vulnerability={"severity": "high"})
                               for n in range(1, 101)], "dependabot")
    assert result["severity_counts_observed"]["high"] == 100
    assert result["status"] == result["severity_status"] == "unmeasured"
    assert result["complete"] is False


@pytest.mark.parametrize("rows", [None, [None], [alert(), alert()], [alert(True)],
                                 [alert(0)], [{"number": 1}], [alert(state="fixed")]])
def test_malformed_or_non_open_alerts_are_not_a_measured_count(rows):
    with pytest.raises(ValueError):
        summarize_alerts(rows, "dependabot")
