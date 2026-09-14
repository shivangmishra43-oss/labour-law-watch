import os
import re
import json
from datetime import datetime


INPUT_DIR = os.path.join(
    "downloads",
    "karnataka",
    "text"
)

METADATA_DIR = os.path.join(
    "downloads",
    "karnataka",
    "metadata"
)

OUTPUT_DIR = os.path.join(
    "downloads",
    "karnataka",
    "extracted"
)


def clean_text(value):
    if not value:
        return ""

    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)

    return value.strip()


def save_json(data, path):
    """
    Save extracted information as UTF-8 JSON.
    """

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def read_text(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


def read_metadata(filename):

    metadata_filename = (
        os.path.splitext(filename)[0]
        + ".json"
    )

    path = os.path.join(
        METADATA_DIR,
        metadata_filename
    )

    if not os.path.exists(path):
        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "  Metadata read error:",
            error
        )

        return {}


def detect_language(text):

    kannada_count = len(
        re.findall(
            r"[\u0C80-\u0CFF]",
            text
        )
    )

    english_count = len(
        re.findall(
            r"[A-Za-z]",
            text
        )
    )

    if kannada_count > english_count:
        return "Kannada"

    if (
        english_count > 0
        and kannada_count > 0
    ):
        return "Kannada / English"

    return "English"


def detect_document_type(
    title,
    text
):

    combined = (
        title
        + " "
        + text[:10000]
    ).lower()

    if (
        "draft code" in combined
        or "draft rules" in combined
        or "draft of the code" in combined
        or "ಕರಡು" in combined
    ):

        return "Draft Rules / Notification"

    if (
        "rules" in combined
        or "ನಿಯಮಗಳು" in combined
    ):

        return "Rules"

    if (
        "act" in combined
        or "ಅಧಿನಿಯಮ" in combined
        or "ಕಾಯ್ದೆ" in combined
    ):

        return "Act / Notification"

    if (
        "minimum wage" in combined
        or "minimum wages" in combined
        or "wages" in combined
        or "wage" in combined
        or "ವೇತನ" in combined
        or "ಕನಿಷ್ಠ ವೇತನ" in combined
    ):

        return "Wage Notification"

    if (
        "corrigendum" in combined
        or "ತಿದ್ದುಪಡಿ" in combined
    ):

        return "Corrigendum"

    return "Notification"


def detect_topic(
    title,
    text
):

    combined = (
        title
        + " "
        + text[:15000]
    ).lower()

    topics = []

    keyword_groups = {

        "Wages / Minimum Wages": [
            "minimum wage",
            "minimum wages",
            "wages",
            "wage",
            "ವೇತನ",
            "ಕನಿಷ್ಠ ವೇತನ",
        ],

        "Social Security": [
            "social security",
            "social welfare",
            "gig worker",
            "gig workers",
            "platform based",
            "platform-based",
            "ಸಾಮಾಜಿಕ ಭದ್ರತೆ",
            "ಗಿಗ್ ಕಾರ್ಮಿಕ",
        ],

        "Industrial Relations": [
            "industrial relations",
            "industrial dispute",
            "trade union",
            "retrenchment",
            "industrial relations code",
            "ಕೈಗಾರಿಕಾ ಸಂಬಂಧ",
            "ಕೈಗಾರಿಕಾ ವಿವಾದ",
        ],

        "Occupational Safety / Working Conditions": [
            "occupational safety",
            "health and working conditions",
            "working conditions",
            "safety",
            "occupational",
            "ಔದ್ಯೋಗಿಕ ಸುರಕ್ಷತೆ",
        ],

        "Motor Transport Workers": [
            "motor transport",
            "transport workers",
            "motor transport workers",
        ],

        "Shops / Establishments": [
            "shops and commercial establishments",
            "commercial establishments",
            "shops and establishments",
        ],

        "Labour Welfare": [
            "labour welfare",
            "labour welfare fund",
            "welfare fund",
            "ಕಾರ್ಮಿಕ ಕಲ್ಯಾಣ",
        ],
    }

    for topic, keywords in keyword_groups.items():

        for keyword in keywords:

            if keyword in combined:

                topics.append(
                    topic
                )

                break

    topics = list(
        dict.fromkeys(
            topics
        )
    )

    if not topics:
        return ["Other Labour Law"]

    return topics


def detect_dates(
    text,
    metadata
):

    dates = []

    patterns = [

        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",

        r"\b\d{1,2}[-/][A-Za-z]{3}[-/]\d{4}\b",

        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",

        r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
        r"[A-Za-z]{3,9}\s+\d{4}\b",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            if match not in dates:

                dates.append(
                    match
                )

    publication_date = metadata.get(
        "publication_date"
    )

    if publication_date:
        publication_date = str(
            publication_date
        )

    return {
        "publication_date":
            publication_date,

        "dates_found":
            dates[:50],
    }


def extract_sections(text):

    sections = []

    patterns = [

        r"\bSection\s+\d+[A-Za-z]?\b",

        r"\bSections\s+\d+[A-Za-z]?"
        r"(?:\s*(?:to|-)\s*\d+[A-Za-z]?)?\b",

        r"\bRule\s+\d+[A-Za-z]?\b",

        r"\bRules\s+\d+[A-Za-z]?"
        r"(?:\s*(?:to|-)\s*\d+[A-Za-z]?)?\b",

        r"\bArticle\s+\d+[A-Za-z]?\b",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:

            cleaned = clean_text(
                match
            )

            if cleaned not in sections:

                sections.append(
                    cleaned
                )

    return sections[:100]


def extract_act_names(
    title,
    text
):

    names = []

    patterns = [

        r"The\s+[A-Z][A-Za-z0-9,\-&'’(). ]{5,150}"
        r"\bAct,\s*\d{4}\b",

        r"The\s+[A-Z][A-Za-z0-9,\-&'’(). ]{5,150}"
        r"\bRules,\s*\d{4}\b",

        r"[A-Z][A-Za-z0-9,\-&'’(). ]{5,150}"
        r"\bCode\s+on\s+[A-Za-z ]+"
        r"\(Karnataka\)\s+Rules,\s*\d{4}\b",
    ]

    combined = (
        title
        + "\n"
        + text[:30000]
    )

    for pattern in patterns:

        matches = re.findall(
            pattern,
            combined
        )

        for match in matches:

            cleaned = clean_text(
                match
            )

            if (
                cleaned
                and cleaned not in names
            ):

                names.append(
                    cleaned
                )

    # Preserve Kannada titles exactly as published.

    if title and any(
        "\u0C80" <= char <= "\u0CFF"
        for char in title
    ):

        names.insert(
            0,
            title
        )

    return list(
        dict.fromkeys(
            names
        )
    )[:30]


def build_summary_input(text):

    text = clean_text(
        text
    )

    maximum_chars = 50000

    if len(text) <= maximum_chars:
        return text

    return text[:maximum_chars]


def process_file(filename):

    text_path = os.path.join(
        INPUT_DIR,
        filename
    )

    text = read_text(
        text_path
    )

    metadata = read_metadata(
        filename
    )

    title = metadata.get(
        "title"
    )

    if not title:

        title = (
            "Karnataka Labour Department Gazette"
        )

    title = clean_text(
        title
    )

    result = {

        "source":
            "Karnataka e-Gazette",

        "jurisdiction":
            "Karnataka",

        "department":
            metadata.get(
                "department",
                "Labour Department"
            ),

        "organization":
            metadata.get(
                "organization",
                "Deputy Secretary Two"
            ),

        "title":
            title,

        "document_number":
            metadata.get(
                "document_number"
            ),

        "gazette_year":
            metadata.get(
                "gazette_year"
            ),

        "document_type":
            detect_document_type(
                title,
                text
            ),

        "topics":
            detect_topic(
                title,
                text
            ),

        "language":
            detect_language(
                text
            ),

        "dates":
            detect_dates(
                text,
                metadata
            ),

        "act_names":
            extract_act_names(
                title,
                text
            ),

        "sections_or_rules":
            extract_sections(
                text
            ),

        "source_url":
            metadata.get(
                "source_url"
            ),

        "document_url":
            metadata.get(
                "document_url"
            ),

        "publication_date":
            metadata.get(
                "publication_date"
            ),

        "effective_date":
            metadata.get(
                "effective_date"
            ),

        "text_file":
            text_path,

        "text_length":
            len(text),

        "ai_input_text":
            build_summary_input(
                text
            ),

        "extracted_at":
            datetime.now().isoformat(),
    }

    return result


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    if not os.path.exists(
        INPUT_DIR
    ):

        print(
            "ERROR: Karnataka text folder not found:"
        )

        print(
            INPUT_DIR
        )

        return

    files = sorted(
        [
            filename
            for filename in os.listdir(
                INPUT_DIR
            )
            if filename.lower().endswith(
                ".txt"
            )
        ]
    )

    print("")
    print("========================================")
    print("      KARNATAKA LEGAL EXTRACTOR")
    print("========================================")
    print("")

    print(
        "Input files:",
        len(files)
    )

    print(
        "Output folder:",
        OUTPUT_DIR
    )

    print("")

    successful = 0
    failed = 0

    for number, filename in enumerate(
        files,
        start=1
    ):

        print(
            f"[{number}/{len(files)}] {filename}"
        )

        try:

            result = process_file(
                filename
            )

            output_filename = (
                os.path.splitext(
                    filename
                )[0]
                + ".json"
            )

            output_path = os.path.join(
                OUTPUT_DIR,
                output_filename
            )

            save_json(
                result,
                output_path
            )

            print(
                "  Title:",
                result["title"]
            )

            print(
                "  Topic:",
                ", ".join(
                    result["topics"]
                )
            )

            print(
                "  Type:",
                result["document_type"]
            )

            print(
                "  Language:",
                result["language"]
            )

            print(
                "  Text:",
                result["text_length"],
                "characters"
            )

            print(
                "  Saved:",
                output_filename
            )

            print("")

            successful += 1

        except Exception as error:

            print(
                "  FAILED:",
                error
            )

            print("")

            failed += 1

    print("")
    print("========================================")
    print("          EXTRACTION COMPLETE")
    print("========================================")
    print("")

    print(
        "Text files processed:",
        len(files)
    )

    print(
        "Successfully processed:",
        successful
    )

    print(
        "Failed:",
        failed
    )

    print("")

    print(
        "Extracted files:",
        OUTPUT_DIR
    )

    print("")


if __name__ == "__main__":
    main()