import os
import sys
import re
from datetime import datetime
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

# pypdf is used to extract text from downloaded Gazette PDFs
from pypdf import PdfReader


# ============================================================
# PROJECT SETUP
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import get_connection, create_database


# ============================================================
# CONFIGURATION
# ============================================================

EGAZETTE_HOME = "https://egazette.gov.in/"

LABOUR_MINISTRY_VALUE = "28"

TODAY = datetime.now()

SEARCH_MONTH = str(TODAY.month)
SEARCH_YEAR = str(TODAY.year)

DOWNLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "downloads",
    "egazette"
)

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(text):
    """
    Clean unnecessary whitespace from text.
    """

    if text is None:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_date(date_text):
    """
    Convert common Gazette date formats into YYYY-MM-DD.
    """

    if not date_text:
        return None

    date_text = clean_text(date_text)

    formats = [
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def split_title_description(text):
    """
    Gazette result cells generally contain:

    Title
    (description)

    This function separates them.
    """

    text = clean_text(text)

    if not text:
        return "", ""

    match = re.match(r"^(.*?)\s*\((.*)\)\s*$", text)

    if match:
        title = clean_text(match.group(1))
        description = clean_text(match.group(2))

        return title, description

    return text, ""


def extract_effective_date(description):
    """
    Look for:

    Date of Applicability : 09/09/2026

    inside the Gazette description.
    """

    if not description:
        return None

    match = re.search(
        r"Date of Applicability\s*:\s*(\d{1,2}/\d{1,2}/\d{4})",
        description,
        re.IGNORECASE
    )

    if match:
        date_value = match.group(1)

        try:
            return datetime.strptime(
                date_value,
                "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


# ============================================================
# LEGAL CLASSIFICATION
# ============================================================

def determine_update_type(title, description):
    """
    Basic rule-based classification.

    We will make this much smarter later.
    """

    combined = f"{title} {description}".lower()

    if "amendment" in combined:
        return "Amendment"

    if "supersession" in combined or "supersede" in combined:
        return "Supersession"

    if "notification" in combined:
        return "Notification"

    if "draft" in combined:
        return "Draft"

    if "order" in combined:
        return "Order"

    if "rules" in combined:
        return "Rules"

    if "scheme" in combined:
        return "Scheme"

    return "Other"


def determine_topic(title, description):
    """
    Basic labour-law topic classification.

    This is intentionally simple for now.
    We will improve it later.
    """

    combined = f"{title} {description}".lower()

    if (
        "provident fund" in combined
        or "epf" in combined
        or "epfo" in combined
    ):
        return "EPF / EPFO"

    if (
        "employee state insurance" in combined
        or "esi" in combined
        or "esic" in combined
    ):
        return "ESI"

    if (
        "social security" in combined
        or "code on social security" in combined
    ):
        return "Social Security"

    if (
        "industrial relations" in combined
        or "industrial dispute" in combined
        or "trade union" in combined
        or "standing orders" in combined
    ):
        return "Industrial Relations"

    if (
        "wage" in combined
        or "minimum wage" in combined
        or "payment of wages" in combined
    ):
        return "Wages"

    if (
        "occupational safety" in combined
        or "health and working conditions" in combined
        or "factory" in combined
        or "factories" in combined
    ):
        return "Occupational Safety & Health"

    if (
        "maternity" in combined
        or "maternity benefit" in combined
    ):
        return "Maternity"

    if (
        "gratuity" in combined
    ):
        return "Gratuity"

    if (
        "apprentice" in combined
        or "apprenticeship" in combined
    ):
        return "Apprentices"

    return "General Labour Law"


def determine_importance(title, description):
    """
    Basic importance classification.

    We will later make this more sophisticated.
    """

    combined = f"{title} {description}".lower()

    high_keywords = [
        "effective",
        "applicable",
        "amendment",
        "supersession",
        "minimum wage",
        "social security",
        "industrial relations",
        "occupational safety",
        "code on wages",
        "code on social security",
        "industrial relations code",
    ]

    for keyword in high_keywords:
        if keyword in combined:
            return "High"

    return "Normal"


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(pdf_path):
    """
    Extract text from every page of a PDF using pypdf.

    Returns:
        extracted text as a single string
    """

    print("")
    print("--------------------------------")
    print("EXTRACTING PDF TEXT")
    print("--------------------------------")

    print("PDF:")
    print(pdf_path)

    try:
        reader = PdfReader(pdf_path)

        print("Number of pages:")
        print(len(reader.pages))

        all_pages = []

        for page_number, page in enumerate(reader.pages, start=1):

            try:
                text = page.extract_text() or ""

            except Exception as error:
                print("")
                print(
                    f"Warning: could not extract page "
                    f"{page_number}: {error}"
                )
                text = ""

            text = text.strip()

            if text:
                all_pages.append(
                    f"--- PAGE {page_number} ---\n{text}"
                )

        full_text = "\n\n".join(all_pages)

        print("")
        print("Extracted characters:")
        print(len(full_text))

        if full_text:
            print("SUCCESS: PDF text extracted.")
        else:
            print("WARNING: PDF contains no extractable text.")

        return full_text

    except Exception as error:

        print("")
        print("ERROR: PDF text extraction failed.")
        print(error)

        return ""


def save_extracted_text(gazette_id, text):
    """
    Save extracted Gazette text as a .txt file.

    This gives us a permanent local copy of the
    machine-readable Gazette text.
    """

    filename = f"{gazette_id}.txt"

    path = os.path.join(
        DOWNLOAD_FOLDER,
        filename
    )

    try:

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(text)

        print("")
        print("Extracted text saved to:")
        print(path)

        return path

    except Exception as error:

        print("")
        print("ERROR: Could not save extracted text.")
        print(error)

        return None


# ============================================================
# DATABASE
# ============================================================

def update_already_exists(gazette_id):
    """
    Check whether this Gazette already exists in our database.

    At the moment we use the Gazette ID as the unique identifier.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM updates
        WHERE source = ?
        AND source_url LIKE ?
        LIMIT 1
        """,
        (
            "eGazette",
            f"%{gazette_id}%"
        )
    )

    row = cursor.fetchone()

    connection.close()

    return row is not None


def save_update(gazette, pdf_url, text_path):
    """
    Save the Gazette metadata into SQLite.
    """

    if update_already_exists(gazette["gazette_id"]):

        print("")
        print("Already exists in database.")
        print("Skipping duplicate.")

        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO updates (
            jurisdiction,
            update_type,
            topic,
            title,
            description,
            publication_date,
            effective_date,
            source,
            source_url,
            document_url,
            importance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Central",
            gazette["update_type"],
            gazette["topic"],
            gazette["title"],
            gazette["description"],
            gazette["publication_date"],
            gazette["effective_date"],
            "eGazette",
            gazette["source_url"],
            pdf_url,
            gazette["importance"]
        )
    )

    update_id = cursor.lastrowid

    connection.commit()
    connection.close()

    print("")
    print(f"Saved to database. ID: {update_id}")

    return update_id


# ============================================================
# RESULT ROW PARSER
# ============================================================

def parse_result_row(row):
    """
    Parse one actual Gazette result row.

    The result table structure we discovered is:

    0 = serial number
    1 = ministry
    2 = N/A
    3 = N/A
    4 = title + description
    5 = category
    6 = part
    7 = issue date
    8 = publish date
    9 = Gazette ID
    10 = size
    """

    cells = row.locator(":scope > td")

    count = cells.count()

    if count < 10:
        return None

    try:

        serial = clean_text(
            cells.nth(0).inner_text()
        )

        if not re.match(r"^\d+\.", serial):
            return None

        ministry = clean_text(
            cells.nth(1).inner_text()
        )

        title_description = clean_text(
            cells.nth(4).inner_text()
        )

        category = clean_text(
            cells.nth(5).inner_text()
        )

        part_section = clean_text(
            cells.nth(6).inner_text()
        )

        issue_date_raw = clean_text(
            cells.nth(7).inner_text()
        )

        publish_date_raw = clean_text(
            cells.nth(8).inner_text()
        )

        gazette_id = clean_text(
            cells.nth(9).inner_text()
        )

        size = clean_text(
            cells.nth(10).inner_text()
        ) if count > 10 else ""

        if not gazette_id:
            return None

        title, description = split_title_description(
            title_description
        )

        issue_date = parse_date(issue_date_raw)
        publication_date = parse_date(publish_date_raw)

        effective_date = extract_effective_date(
            description
        )

        if not effective_date:
            effective_date = issue_date

        update_type = determine_update_type(
            title,
            description
        )

        topic = determine_topic(
            title,
            description
        )

        importance = determine_importance(
            title,
            description
        )

        return {
            "serial": serial,
            "ministry": ministry,
            "title": title,
            "description": description,
            "category": category,
            "part_section": part_section,
            "issue_date": issue_date,
            "publication_date": publication_date,
            "gazette_id": gazette_id,
            "size": size,
            "effective_date": effective_date,
            "update_type": update_type,
            "topic": topic,
            "importance": importance,
            "source_url": (
                f"https://egazette.gov.in/"
                f"SearchMinistry.aspx"
            )
        }

    except Exception as error:

        print("")
        print("ERROR parsing Gazette row:")
        print(error)

        return None


# ============================================================
# PDF DOWNLOAD
# ============================================================

def is_real_pdf(body):
    """
    A genuine PDF should begin with %PDF-.
    """

    if not body:
        return False

    return body.startswith(b"%PDF-")


def save_pdf_body(gazette_id, body):
    """
    Save PDF bytes to disk.
    """

    filename = f"{gazette_id}.pdf"

    path = os.path.join(
        DOWNLOAD_FOLDER,
        filename
    )

    with open(path, "wb") as file:
        file.write(body)

    return path


def download_gazette(page, context, gazette_id, button_index):
    """
    Download the real PDF.

    eGazette does NOT directly return the PDF when the
    search-result PDF button is clicked.

    Instead:

        PDF button
            ↓
        ViewPDF.aspx
            ↓
        iframe
            ↓
        ../WriteReadData/YYYY/NUMBER.pdf

    We therefore:

        1. Click the PDF button.
        2. Catch the popup.
        3. Read the iframe src.
        4. Convert it to an absolute URL.
        5. Request that URL through Playwright.
        6. Verify the response starts with %PDF-.
        7. Save the PDF.
    """

    print("")
    print("--------------------------------")
    print("DOWNLOADING GAZETTE")
    print(f"Gazette ID: {gazette_id}")
    print(f"Button index: {button_index}")
    print("--------------------------------")

    pdf_url = None
    popup = None

    try:

        buttons = page.locator(
            "#gvGazetteList input[type='image']"
        )

        button_count = buttons.count()

        print(f"Download buttons found: {button_count}")

        if button_index >= button_count:

            print("ERROR: Button index does not exist.")

            return None, None

        button = buttons.nth(button_index)

        print(
            "Button ID:",
            button.get_attribute("id")
        )

        print(
            "Button name:",
            button.get_attribute("name")
        )

        print("")
        print("Clicking PDF button...")

        with page.expect_popup(timeout=15000) as popup_info:

            button.click()

        popup = popup_info.value

        print("")
        print("SUCCESS: New browser window detected!")

        popup.wait_for_load_state(
            "domcontentloaded",
            timeout=30000
        )

        print("")
        print("Popup URL:")
        print(popup.url)

        print("")
        print("Looking for PDF iframe...")

        iframe = popup.locator(
            "#framePDFDisplay"
        )

        iframe.wait_for(
            state="attached",
            timeout=30000
        )

        iframe_src = iframe.get_attribute("src")

        print("")
        print("Iframe src:")
        print(iframe_src)

        if not iframe_src:

            print("ERROR: PDF iframe has no src.")

            return None, None

        pdf_url = popup.evaluate(
            """
            (src) => new URL(
                src,
                window.location.href
            ).href
            """,
            iframe_src
        )

        print("")
        print("Actual PDF URL:")
        print(pdf_url)

        print("")
        print("Requesting actual PDF...")

        response = context.request.get(
            pdf_url,
            timeout=60000
        )

        body = response.body()

        print("")
        print("PDF response status:")
        print(response.status)

        print("PDF response Content-Type:")
        print(
            response.headers.get(
                "content-type",
                ""
            )
        )

        print("PDF response size:")
        print(len(body))

        print("First bytes:")
        print(body[:20])

        if not is_real_pdf(body):

            print("")
            print("ERROR: Response is NOT a real PDF.")

            diagnostic_path = os.path.join(
                DOWNLOAD_FOLDER,
                f"{gazette_id}_pdf_response_failed.html"
            )

            with open(
                diagnostic_path,
                "wb"
            ) as file:

                file.write(body)

            print("")
            print("Diagnostic response saved to:")
            print(diagnostic_path)

            return None, pdf_url

        pdf_path = save_pdf_body(
            gazette_id,
            body
        )

        print("")
        print("SUCCESS: REAL PDF DOWNLOADED!")

        print("Saved to:")
        print(pdf_path)

        print("File size:")
        print(os.path.getsize(pdf_path))

        return pdf_path, pdf_url

    except Exception as error:

        print("")
        print("ERROR: PDF download failed.")
        print(error)

        return None, pdf_url

    finally:

        if popup is not None:

            try:
                popup.close()
            except Exception:
                pass


# ============================================================
# MAIN COLLECTOR
# ============================================================

def run_collector():

    print("")
    print("====================================")
    print("      LABOUR LAW WATCH")
    print("====================================")
    print("")
    print("eGAZETTE COLLECTOR")
    print("")
    print(f"Automatic search month: {SEARCH_MONTH}")
    print(f"Automatic search year: {SEARCH_YEAR}")
    print(
        f"Labour Ministry value: "
        f"{LABOUR_MINISTRY_VALUE}"
    )

    create_database()

    with sync_playwright() as playwright:

        print("")
        print("Launching Chromium...")

        browser = playwright.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            ignore_https_errors=True
        )

        page = context.new_page()

        try:

            # ==================================================
            # OPEN HOME PAGE
            # ==================================================

            print("")
            print("Opening eGazette homepage...")

            page.goto(
                EGAZETTE_HOME,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("Homepage loaded.")
            print("Current URL:")
            print(page.url)

            # ==================================================
            # SEARCH GAZETTE
            # ==================================================

            print("")
            print("Looking for Search Gazette...")

            search_link = page.get_by_text(
                "Search Gazette",
                exact=True
            ).first

            search_link.wait_for(
                state="visible",
                timeout=30000
            )

            print("Search Gazette found.")

            search_link.click()

            page.wait_for_load_state(
                "domcontentloaded",
                timeout=30000
            )

            print("Current URL:")
            print(page.url)

            # ==================================================
            # SEARCH BY MINISTRY
            # ==================================================

            print("")
            print("Looking for Search by Ministry...")

            ministry_link = page.get_by_text(
                "Search by Ministry",
                exact=True
            ).first

            ministry_link.wait_for(
                state="visible",
                timeout=30000
            )

            print("Search by Ministry found.")

            ministry_link.click()

            page.wait_for_load_state(
                "domcontentloaded",
                timeout=30000
            )

            print("Current URL:")
            print(page.url)

            # ==================================================
            # SELECT MINISTRY
            # ==================================================

            print("")
            print("Waiting for Ministry dropdown...")

            ministry_dropdown = page.locator(
                "#ddlMinistry"
            )

            ministry_dropdown.wait_for(
                state="visible",
                timeout=30000
            )

            ministry_dropdown.select_option(
                LABOUR_MINISTRY_VALUE
            )

            print(
                "Ministry selected:",
                ministry_dropdown.locator(
                    "option:checked"
                ).inner_text()
            )

            # ==================================================
            # SELECT MONTH
            # ==================================================

            print("")
            print("Looking for month dropdown...")

            month_dropdown = page.locator(
                "#ddlmonth"
            )

            month_dropdown.wait_for(
                state="visible",
                timeout=30000
            )

            month_dropdown.select_option(
                SEARCH_MONTH
            )

            print(
                "Month selected:",
                month_dropdown.locator(
                    "option:checked"
                ).inner_text()
            )

            # ==================================================
            # SELECT YEAR
            # ==================================================

            print("")
            print("Waiting for year dropdown...")

            year_dropdown = page.locator(
                "#ddlyear"
            )

            year_dropdown.wait_for(
                state="visible",
                timeout=30000
            )

            year_dropdown.select_option(
                SEARCH_YEAR
            )

            print(
                "Year selected:",
                year_dropdown.locator(
                    "option:checked"
                ).inner_text()
            )

            # ==================================================
            # SUBMIT SEARCH
            # ==================================================

            print("")
            print("Submitting eGazette search...")

            submit_button = page.locator(
                "input[name='ImgSubmitDetails']"
            )

            submit_button.wait_for(
                state="visible",
                timeout=30000
            )

            print("Submit button found.")

            submit_button.click()

            # ==================================================
            # WAIT FOR RESULTS
            # ==================================================

            print("")
            print("Waiting for search results...")

            page.locator(
                "#gvGazetteList"
            ).wait_for(
                state="visible",
                timeout=60000
            )

            print("Search results page loaded.")

            print("Current URL:")
            print(page.url)

            # ==================================================
            # READ RESULTS
            # ==================================================

            table = page.locator(
                "#gvGazetteList"
            )

            rows = table.locator(
                "tr"
            )

            row_count = rows.count()

            print("")
            print(
                "Rows found:",
                row_count
            )

            gazettes = []

            for row_index in range(row_count):

                row = rows.nth(row_index)

                gazette = parse_result_row(
                    row
                )

                if gazette is None:
                    continue

                print("")
                print(
                    f"Gazette "
                    f"{len(gazettes) + 1}:"
                )

                print(
                    "Title:",
                    gazette["title"]
                )

                print(
                    "Gazette ID:",
                    gazette["gazette_id"]
                )

                print(
                    "Effective Date:",
                    gazette["effective_date"]
                )

                print(
                    "Topic:",
                    gazette["topic"]
                )

                print(
                    "Update Type:",
                    gazette["update_type"]
                )

                print(
                    "Importance:",
                    gazette["importance"]
                )

                gazettes.append(
                    gazette
                )

            print("")
            print("====================================")
            print(
                "TOTAL ACTUAL GAZETTES FOUND:",
                len(gazettes)
            )
            print("====================================")

            # ==================================================
            # PROCESS EVERY GAZETTE
            # ==================================================

            for index, gazette in enumerate(
                gazettes
            ):

                print("")
                print("====================================")
                print(
                    f"PROCESSING RESULT "
                    f"{index + 1} OF "
                    f"{len(gazettes)}"
                )
                print("====================================")

                print(
                    "Gazette:",
                    gazette["title"]
                )

                print(
                    "Gazette ID:",
                    gazette["gazette_id"]
                )

                # ----------------------------------------------
                # DOWNLOAD PDF
                # ----------------------------------------------

                pdf_path, pdf_url = download_gazette(
                    page,
                    context,
                    gazette["gazette_id"],
                    index
                )

                if not pdf_path:

                    print("")
                    print(
                        "PDF download failed."
                    )

                    print(
                        "NOT saving Gazette "
                        "to database."
                    )

                    continue

                # ----------------------------------------------
                # EXTRACT PDF TEXT
                # ----------------------------------------------

                extracted_text = extract_pdf_text(
                    pdf_path
                )

                text_path = None

                if extracted_text:

                    text_path = save_extracted_text(
                        gazette["gazette_id"],
                        extracted_text
                    )

                else:

                    print("")
                    print(
                        "WARNING: No text extracted."
                    )

                # ----------------------------------------------
                # SAVE DATABASE RECORD
                # ----------------------------------------------

                save_update(
                    gazette,
                    pdf_url,
                    text_path
                )

            # ==================================================
            # FINISHED
            # ==================================================

            print("")
            print("====================================")
            print("       COLLECTOR FINISHED")
            print("====================================")

            print(
                "Gazettes found:",
                len(gazettes)
            )

            print("Download folder:")
            print(DOWNLOAD_FOLDER)

        except Exception as error:

            print("")
            print("====================================")
            print("             ERROR")
            print("====================================")

            print(
                repr(error)
            )

        finally:

            print("")
            print("Closing browser...")

            browser.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    run_collector()