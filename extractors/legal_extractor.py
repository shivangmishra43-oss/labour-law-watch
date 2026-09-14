import os
import re
import json
from datetime import datetime


# ============================================================
# LABOUR LAW WATCH
# STEP 6 - LEGAL INFORMATION EXTRACTOR
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_FOLDER = os.path.join(
    BASE_DIR,
    "downloads",
    "egazette"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "downloads",
    "egazette",
    "extracted"
)


# ============================================================
# FOLDER SETUP
# ============================================================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ============================================================
# BASIC TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Cleans extracted PDF text while preserving useful legal content.
    """

    if not text:
        return ""

    # Replace Windows line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# EXTRACT GAZETTE ID
# ============================================================

def extract_gazette_id(filename):
    """
    Extracts Gazette ID from filename.

    Example:
    CG-DL-E-09092026-276091.txt

    Returns:
    CG-DL-E-09092026-276091
    """

    name = os.path.splitext(filename)[0]

    return name


# ============================================================
# EXTRACT NOTIFICATION NUMBER
# ============================================================

def extract_notification_number(text):
    """
    Attempts to identify notification/order numbers.

    Examples:
    S.O. 5009(E)
    G.S.R. 123(E)
    S.O. 2523(E)
    """

    patterns = [
        r"\bS\.?\s*O\.?\s*[\-]?\s*\d+(?:\s*\([A-Z]\))?",
        r"\bG\.?\s*S\.?\s*R\.?\s*[\-]?\s*\d+(?:\s*\([A-Z]\))?",
        r"\bS\.O\.\s*\d+\s*\([A-Z]\)",
        r"\bG\.S.R\.\s*\d+\s*\([A-Z]\)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip()

    return None


# ============================================================
# EXTRACT ACT NAME
# ============================================================

def extract_act_name(text):
    """
    Attempts to identify the principal Act mentioned in the Gazette.
    """

    act_patterns = [
        r"Employees[’']?\s+Provident\s+Funds\s+and\s+Miscellaneous\s+Provisions\s+Act,\s*1952",
        r"Code\s+on\s+Social\s+Security,\s*2020",
        r"Industrial\s+Disputes\s+Act,\s*1947",
        r"Industrial\s+Relations\s+Code,\s*2020",
        r"Occupational\s+Safety,\s+Health\s+and\s+Working\s+Conditions\s+Code,\s*2020",
        r"Code\s+on\s+Wages,\s*2019",
        r"Minimum\s+Wages\s+Act,\s*1948",
        r"Payment\s+of\s+Wages\s+Act,\s*1936",
        r"Factories\s+Act,\s*1948",
        r"Employees[’']?\s+State\s+Insurance\s+Act,\s*1948",
        r"Payment\s+of\s+Gratuity\s+Act,\s*1972",
        r"Maternity\s+Benefit\s+Act,\s*1961",
        r"Contract\s+Labour\s+\(Regulation\s+and\s+Abolition\)\s+Act,\s*1970",
        r"Child\s+and\s+Adolescent\s+Labour\s+\(Prohibition\s+and\s+Regulation\)\s+Act,\s*1986",
        r"Apprentices\s+Act,\s*1961",
        r"Trade\s+Unions\s+Act,\s*1926"
    ]

    for pattern in act_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip()

    return None


# ============================================================
# EXTRACT SECTIONS / RULES
# ============================================================

def extract_sections_rules(text):
    """
    Attempts to identify sections, rules, clauses and sub-rules.
    """

    results = []

    patterns = [
        r"Section\s+\d+(?:\s*\([^)]+\))*",
        r"Sections\s+\d+(?:\s*(?:and|to|-)\s*\d+)?",
        r"Rule\s+\d+(?:\s*\([^)]+\))*",
        r"Rules\s+\d+(?:\s*(?:and|to|-)\s*\d+)?",
        r"clause\s+\([a-z0-9]+\)",
        r"sub-rule\s+\([a-z0-9]+\)"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for match in matches:

            cleaned = re.sub(
                r"\s+",
                " ",
                match
            ).strip()

            if cleaned not in results:
                results.append(cleaned)

    return results


# ============================================================
# EXTRACT DATE
# ============================================================

def normalise_date(date_string):
    """
    Converts common Indian Gazette date formats
    into YYYY-MM-DD where possible.
    """

    if not date_string:
        return None

    date_string = date_string.strip()

    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y"
    ]

    for fmt in formats:

        try:

            date_value = datetime.strptime(
                date_string,
                fmt
            )

            return date_value.strftime("%Y-%m-%d")

        except ValueError:
            continue

    return None


def extract_dates(text):
    """
    Extracts dates appearing in the Gazette text.
    """

    dates = []

    patterns = [
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4}\b",
        r"\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4}\b"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for match in matches:

            normalised = normalise_date(match)

            if normalised and normalised not in dates:
                dates.append(normalised)

    return dates


# ============================================================
# EXTRACT EFFECTIVE DATE
# ============================================================

def extract_effective_date(text):
    """
    Looks for wording indicating when a notification comes
    into force / takes effect.
    """

    patterns = [

        r"shall come into force on\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",

        r"shall come into force\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",

        r"shall take effect from\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",

        r"with effect from\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",

        r"effective from\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            date_value = normalise_date(
                match.group(1)
            )

            if date_value:
                return date_value

    return None


# ============================================================
# DETERMINE UPDATE TYPE
# ============================================================

def determine_update_type(text):
    """
    Determines the broad legal nature of the update.
    """

    text_lower = text.lower()

    if "supersession" in text_lower:
        return "Supersession"

    if "amendment" in text_lower:
        return "Amendment"

    if "substitution" in text_lower:
        return "Substitution"

    if "notification" in text_lower:
        return "Notification"

    if "rules" in text_lower and "made" in text_lower:
        return "Rules"

    if "order" in text_lower:
        return "Order"

    if "corrigendum" in text_lower:
        return "Corrigendum"

    return "Other"


# ============================================================
# DETERMINE TOPIC
# ============================================================

def determine_topic(text):
    """
    Determines a broad labour-law topic.
    """

    text_lower = text.lower()

    topic_keywords = [

        (
            "EPF / EPFO",
            [
                "provident fund",
                "epfo",
                "employees' provident funds",
                "employees’ provident funds",
                "epf"
            ]
        ),

        (
            "ESI / ESIC",
            [
                "employee state insurance",
                "employees' state insurance",
                "employees’ state insurance",
                "esic",
                "esi"
            ]
        ),

        (
            "Social Security",
            [
                "code on social security",
                "social security"
            ]
        ),

        (
            "Wages",
            [
                "minimum wages",
                "code on wages",
                "wages"
            ]
        ),

        (
            "Industrial Relations",
            [
                "industrial relations code",
                "industrial disputes",
                "trade union",
                "retrenchment",
                "strike",
                "lockout"
            ]
        ),

        (
            "Occupational Safety & Health",
            [
                "occupational safety",
                "health and working conditions",
                "factories act",
                "safety"
            ]
        ),

        (
            "Gratuity",
            [
                "payment of gratuity",
                "gratuity"
            ]
        ),

        (
            "Maternity",
            [
                "maternity benefit",
                "maternity"
            ]
        ),

        (
            "Contract Labour",
            [
                "contract labour",
                "contract labourers"
            ]
        ),

        (
            "Apprentices",
            [
                "apprentices act",
                "apprenticeship"
            ]
        )
    ]

    for topic, keywords in topic_keywords:

        for keyword in keywords:

            if keyword in text_lower:
                return topic

    return "Other"


# ============================================================
# DETERMINE IMPORTANCE
# ============================================================

def determine_importance(
    text,
    update_type,
    effective_date
):
    """
    Gives a preliminary importance classification.

    This is NOT the final AI importance score.
    """

    text_lower = text.lower()

    high_priority_terms = [
        "shall come into force",
        "with effect from",
        "effective from",
        "supersession",
        "amendment",
        "substitution",
        "contribution",
        "wages",
        "minimum wages",
        "provident fund",
        "social security"
    ]

    for term in high_priority_terms:

        if term in text_lower:
            return "High"

    if update_type in [
        "Amendment",
        "Supersession",
        "Substitution",
        "Rules"
    ]:
        return "High"

    if effective_date:
        return "High"

    return "Normal"


# ============================================================
# EXTRACT IMPORTANT TEXT
# ============================================================

def extract_key_sentences(text):
    """
    Pulls sentences which are likely to contain substantive
    legal information.

    This is intentionally basic.
    AI summarisation will be added later.
    """

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    keywords = [
        "amend",
        "substitut",
        "insert",
        "omit",
        "shall",
        "come into force",
        "with effect",
        "supersede",
        "provided",
        "notwithstanding",
        "contribution",
        "investment",
        "employer",
        "employee",
        "establishment",
        "notification"
    ]

    important = []

    for sentence in sentences:

        sentence_clean = re.sub(
            r"\s+",
            " ",
            sentence
        ).strip()

        if len(sentence_clean) < 30:
            continue

        sentence_lower = sentence_clean.lower()

        if any(
            keyword in sentence_lower
            for keyword in keywords
        ):

            if sentence_clean not in important:
                important.append(sentence_clean)

    # Avoid producing an enormous output
    return important[:25]


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_legal_information(
    text,
    filename
):
    """
    Extracts structured legal information from a Gazette.
    """

    cleaned_text = clean_text(text)

    gazette_id = extract_gazette_id(
        filename
    )

    notification_number = extract_notification_number(
        cleaned_text
    )

    act_name = extract_act_name(
        cleaned_text
    )

    sections_rules = extract_sections_rules(
        cleaned_text
    )

    dates = extract_dates(
        cleaned_text
    )

    effective_date = extract_effective_date(
        cleaned_text
    )

    update_type = determine_update_type(
        cleaned_text
    )

    topic = determine_topic(
        cleaned_text
    )

    importance = determine_importance(
        cleaned_text,
        update_type,
        effective_date
    )

    key_sentences = extract_key_sentences(
        cleaned_text
    )

    result = {

        "gazette_id": gazette_id,

        "notification_number": notification_number,

        "act_name": act_name,

        "sections_rules": sections_rules,

        "publication_dates_found": dates,

        "effective_date": effective_date,

        "update_type": update_type,

        "topic": topic,

        "importance": importance,

        "key_sentences": key_sentences
    }

    return result


# ============================================================
# PROCESS ONE FILE
# ============================================================

def process_text_file(filepath):
    """
    Reads one .txt file and creates a JSON file containing
    extracted legal information.
    """

    filename = os.path.basename(filepath)

    print("")
    print("====================================")
    print("PROCESSING TEXT FILE")
    print("====================================")

    print("File:")
    print(filepath)

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:

            text = file.read()

    except Exception as error:

        print("")
        print("ERROR READING FILE:")
        print(error)

        return None

    print("")
    print("Characters:")
    print(len(text))

    result = extract_legal_information(
        text,
        filename
    )

    output_filename = (
        os.path.splitext(filename)[0]
        + ".json"
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        output_filename
    )

    try:

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False
            )

    except Exception as error:

        print("")
        print("ERROR SAVING JSON:")
        print(error)

        return result

    print("")
    print("Extracted information:")
    print("")
    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )

    print("")
    print("Saved JSON:")
    print(output_path)

    return result


# ============================================================
# PROCESS ALL TEXT FILES
# ============================================================

def run_extractor():

    print("")
    print("====================================")
    print("       LABOUR LAW WATCH")
    print("====================================")
    print("")
    print("STEP 6")
    print("LEGAL INFORMATION EXTRACTOR")
    print("")

    print("Looking for extracted Gazette text...")
    print("Folder:")
    print(TEXT_FOLDER)

    if not os.path.exists(TEXT_FOLDER):

        print("")
        print("ERROR:")
        print("Text folder does not exist.")

        return

    text_files = []

    for filename in os.listdir(TEXT_FOLDER):

        if not filename.lower().endswith(".txt"):
            continue

        filepath = os.path.join(
            TEXT_FOLDER,
            filename
        )

        if os.path.isfile(filepath):
            text_files.append(filepath)

    text_files.sort()

    print("")
    print("Text files found:")
    print(len(text_files))

    if len(text_files) == 0:

        print("")
        print("No .txt files found.")
        return

    successful = 0

    for index, filepath in enumerate(
        text_files,
        start=1
    ):

        print("")
        print("------------------------------------")
        print(
            f"FILE {index} OF {len(text_files)}"
        )
        print("------------------------------------")

        result = process_text_file(
            filepath
        )

        if result is not None:
            successful += 1

    print("")
    print("====================================")
    print("       EXTRACTOR FINISHED")
    print("====================================")

    print("")
    print("Text files processed:")
    print(len(text_files))

    print("Successfully processed:")
    print(successful)

    print("")
    print("JSON output folder:")
    print(OUTPUT_FOLDER)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    run_extractor()