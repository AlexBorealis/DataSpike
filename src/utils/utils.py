from typing import Optional


def extract_country_from_mrz(mrz_text: str) -> Optional[str]:
    lines = mrz_text.split("\n")

    if not lines or len(lines[0]) < 5:
        return None

    country = lines[0][2:5]

    return country if country.isalpha() and country.isupper() else None
