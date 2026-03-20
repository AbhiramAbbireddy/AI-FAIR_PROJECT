from src.resume_parser import (
    extract_email,
    extract_experience_years,
    extract_phone,
)


def test_extract_email():
    text = "Reach me at rahul.sharma@gmail.com for interview scheduling."
    assert extract_email(text) == "rahul.sharma@gmail.com"


def test_extract_phone_with_country_code():
    text = "Contact: +91-9876543210 or office line later."
    assert extract_phone(text) == "+91-9876543210"


def test_extract_phone_without_country_code():
    text = "Mobile: (987) 654-3210"
    assert extract_phone(text) == "9876543210"


def test_extract_experience_years_prefers_largest_match():
    text = (
        "I have 3 years of experience in backend development and over 5 years "
        "of total software experience across internships and full-time roles."
    )
    assert extract_experience_years(text) == 5


def test_extract_experience_years_returns_none_when_missing():
    text = "Python, SQL, Docker, AWS"
    assert extract_experience_years(text) is None
