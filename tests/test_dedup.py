"""Tests for the deduplication engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.dedup import Deduplicator


def test_clean_url():
    d = Deduplicator()
    assert d.clean_url("https://linkedin.com/in/john-doe/") == "https://linkedin.com/in/john-doe"
    assert d.clean_url("https://linkedin.com/in/john-doe?trk=abc") == "https://linkedin.com/in/john-doe"
    assert d.clean_url("  https://linkedin.com/in/jane  ") == "https://linkedin.com/in/jane"


def test_duplicate_url_detection():
    d = Deduplicator()
    d.add_url("https://linkedin.com/in/john-doe/")
    assert d.is_duplicate_url("https://linkedin.com/in/john-doe") is True
    assert d.is_duplicate_url("https://linkedin.com/in/john-doe/?trk=xyz") is True
    assert d.is_duplicate_url("https://linkedin.com/in/jane-doe") is False


def test_duplicate_company_detection():
    d = Deduplicator()
    d.seen_companies = {"visa", "swiggy", "rackspace technology"}
    assert d.is_duplicate_company("Visa") is True
    assert d.is_duplicate_company("Swiggy") is True
    assert d.is_duplicate_company("Rackspace") is True  # partial match
    assert d.is_duplicate_company("NewCorp") is False


def test_deduplicate_contacts():
    d = Deduplicator()
    contacts = [
        {"company": "A", "name": "John", "url": "https://linkedin.com/in/john"},
        {"company": "A", "name": "John Dup", "url": "https://linkedin.com/in/john/"},
        {"company": "B", "name": "Jane", "url": "https://linkedin.com/in/jane"},
        {"company": "C", "name": "Bad", "url": "https://linkedin.com/edit/forms/123"},
    ]
    result = d.deduplicate_contacts(contacts)
    assert len(result) == 2
    assert result[0]["name"] == "John"
    assert result[1]["name"] == "Jane"


def test_company_filter():
    from src.utils.company_filter import CompanyFilter
    cf = CompanyFilter()
    assert cf.should_skip("ABC Staffing Solutions") is True
    assert cf.should_skip("Gamyam Technologies") is True
    assert cf.should_skip("Visa") is False

    cf.existing = {"visa"}
    assert cf.should_skip("Visa") is True
    assert cf.should_skip("Swiggy") is False


if __name__ == "__main__":
    test_clean_url()
    test_duplicate_url_detection()
    test_duplicate_company_detection()
    test_deduplicate_contacts()
    test_company_filter()
    print("All tests passed!")
