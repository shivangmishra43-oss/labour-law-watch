import os
import re
import json
import time
from datetime import datetime
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright
from pypdf import PdfReader


BASE_URL = "https://erajyapatra.karnataka.gov.in"
HOME_URL = BASE_URL + "/"

DOWNLOAD_DIR = os.path.join(
    "downloads",
    "karnataka"
)

PDF_DIR = os.path.join(
    DOWNLOAD_DIR,
    "pdf"
)

TEXT_DIR = os.path.join(
    DOWNLOAD_DIR,
    "text"
)

METADATA_DIR = os.path.join(
    DOWNLOAD_DIR,
    "metadata"
)


DEPARTMENT_VALUE = "1340"
DEPARTMENT_NAME = "Labour Department"

ORGANIZATION_VALUE = "2239"
ORGANIZATION_NAME = "Deputy Secretary Two"


def make_directories():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(TEXT_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)


def clean_text(value):
    if value is None:
        return ""

    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def safe_filename(value):
    value = clean_text(value)

    value = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        value
    )

    value = value[:150]

    if not value:
        value = "karnataka_gazette"

    return value


def extract_pdf_path(html):
    """
    Karnataka returns an HTML response after the PDF button POST.

    The response contains JavaScript such as:

    window.open('../WriteReadData/2026/11284.pdf', ...)

    Extract that PDF path.
    """

    patterns = [
        r"window\.open\(\s*['\"]([^'\"]*WriteReadData[^'\"]+\.pdf)['\"]",
        r"window\.open\(\s*['\"]([^'\"]+\.pdf)['\"]",
        r"['\"]([^'\"]*WriteReadData[^'\"]+\.pdf)['\"]",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            html,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


def normalize_pdf_url(pdf_path):

    if not pdf_path:
        return None

    pdf_path = pdf_path.replace(
        "\\",
        "/"
    )

    return urljoin(
        BASE_URL + "/",
        pdf_path
    )


def extract_pdf_text(pdf_path):

    try:

        reader = PdfReader(
            pdf_path
        )

        pages = []

        for page in reader.pages:

            try:

                text = page.extract_text()

                if text:
                    pages.append(text)

            except Exception as error:

                print(
                    "  Warning: page extraction failed:",
                    error
                )

        return "\n\n".join(
            pages
        ).strip()

    except Exception as error:

        print(
            "  PDF text extraction failed:",
            error
        )

        return ""


def guess_title(values):

    candidates = []

    for value in values:

        value = clean_text(
            value
        )

        if not value:
            continue

        lower = value.lower()

        if value.isdigit():
            continue

        if re.fullmatch(
            r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
            value
        ):
            continue

        if re.fullmatch(
            r"\d{1,2}[-/][A-Za-z]{3}[-/]\d{4}",
            value
        ):
            continue

        if lower in {
            "daily",
            "weekly",
            "extra ordinary",
            "extraordinary",
            "special",
        }:
            continue

        if len(value) >= 8:
            candidates.append(
                value
            )

    if not candidates:

        return (
            "Karnataka Labour Department Gazette"
        )

    return max(
        candidates,
        key=len
    )


def guess_date(values):

    patterns = [

        r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",

        r"\d{1,2}[-/][A-Za-z]{3}[-/]\d{4}",

        r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}",
    ]

    for value in values:

        for pattern in patterns:

            match = re.search(
                pattern,
                value
            )

            if not match:
                continue

            raw_date = match.group(
                0
            )

            formats = [

                "%d-%m-%Y",
                "%d/%m/%Y",

                "%d-%b-%Y",
                "%d/%b/%Y",

                "%d %B %Y",
                "%d %b %Y",
            ]

            for fmt in formats:

                try:

                    return datetime.strptime(
                        raw_date,
                        fmt
                    ).strftime(
                        "%Y-%m-%d"
                    )

                except ValueError:
                    pass

    return None


def guess_gazette_type(values):

    text = " ".join(
        values
    ).lower()

    if (
        "extra ordinary" in text
        or "extraordinary" in text
    ):
        return "Notification"

    if "daily" in text:
        return "Notification"

    if "weekly" in text:
        return "Notification"

    return "Notification"


def save_text(text, path):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            text
        )


def save_json(data, path):

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


def find_department_search_button(page):

    """
    The Karnataka site uses ASP.NET Web Forms.

    Instead of relying exclusively on one selector,
    inspect the actual buttons on the page and identify
    the Department-wise Search button.
    """

    selectors = [

        "#ContentPlaceHolder1_Button2",

        "input[type='submit']",

        "input[type='button']",

        "button",

        "a",
    ]

    for selector in selectors:

        elements = page.locator(
            selector
        )

        count = elements.count()

        for index in range(count):

            try:

                element = elements.nth(
                    index
                )

                element_id = (
                    element.get_attribute(
                        "id"
                    )
                    or ""
                )

                element_name = (
                    element.get_attribute(
                        "name"
                    )
                    or ""
                )

                value = (
                    element.get_attribute(
                        "value"
                    )
                    or ""
                )

                text = clean_text(
                    element.inner_text()
                )

                combined = (
                    element_id
                    + " "
                    + element_name
                    + " "
                    + value
                    + " "
                    + text
                ).lower()

                if (
                    "button2" in combined
                    or "department" in combined
                    or "department-wise" in combined
                    or "department wise" in combined
                ):

                    return element

            except Exception:
                continue

    return None


def find_result_table(page):

    tables = page.locator(
        "table"
    )

    count = tables.count()

    for index in range(count):

        table = tables.nth(
            index
        )

        try:

            html = table.inner_html()

            if (
                "imgbtndownload"
                in html
            ):

                return table

        except Exception:
            continue

    return None


def extract_result_metadata(table):

    results = []

    rows = table.locator(
        "tr"
    )

    row_count = rows.count()

    for row_index in range(
        row_count
    ):

        row = rows.nth(
            row_index
        )

        try:

            cells = row.locator(
                "td"
            )

            cell_count = cells.count()

            if cell_count == 0:
                continue

            values = []

            for cell_index in range(
                cell_count
            ):

                value = clean_text(
                    cells.nth(
                        cell_index
                    ).inner_text()
                )

                values.append(
                    value
                )

            pdf_buttons = row.locator(
                'input[id*="imgbtndownload"]'
            )

            if pdf_buttons.count() == 0:
                continue

            button = pdf_buttons.first

            results.append(
                {
                    "row_index": row_index,

                    "values": values,

                    "button_id":
                        button.get_attribute(
                            "id"
                        ),

                    "button_name":
                        button.get_attribute(
                            "name"
                        ),
                }
            )

        except Exception as error:

            print(
                f"  Warning: could not read row {row_index}:",
                error
            )

    return results


def download_pdf(
    context,
    pdf_url,
    destination
):

    try:

        response = context.request.get(
            pdf_url,
            timeout=120000
        )

        if not response.ok:

            print(
                "  PDF request failed:",
                response.status
            )

            return False

        body = response.body()

        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
            .lower()
        )

        if not body.startswith(
            b"%PDF-"
        ):

            print(
                "  ERROR: response was not a PDF."
            )

            print(
                "  Content-Type:",
                content_type
            )

            print(
                "  First bytes:",
                body[:30]
            )

            return False

        with open(
            destination,
            "wb"
        ) as file:

            file.write(
                body
            )

        print(
            "  Downloaded:",
            f"{len(body):,}",
            "bytes"
        )

        return True

    except Exception as error:

        print(
            "  PDF download error:",
            error
        )

        return False


def collect():

    make_directories()

    print("")
    print("========================================")
    print("     KARNATAKA E-GAZETTE COLLECTOR")
    print("========================================")
    print("")
    print(
        "Department:",
        DEPARTMENT_NAME
    )
    print(
        "Organization:",
        ORGANIZATION_NAME
    )
    print("")

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            ignore_https_errors=True
        )

        page = context.new_page()

        try:

            # ---------------------------------
            # STEP 1
            # ---------------------------------

            print(
                "1. Opening Karnataka e-Gazette..."
            )

            page.goto(
                HOME_URL,
                wait_until="domcontentloaded",
                timeout=120000
            )

            time.sleep(2)

            print(
                "   Loaded:",
                page.url
            )

            # ---------------------------------
            # STEP 2
            # ---------------------------------

            print("")
            print(
                "2. Opening Gazette Search..."
            )

            # We know from our successful manual test
            # that the homepage uses this ASP.NET
            # postback.

            page.evaluate(
                "__doPostBack('sgzt','')"
            )

            page.wait_for_load_state(
                "domcontentloaded",
                timeout=120000
            )

            time.sleep(3)

            print(
                "   Search page:",
                page.url
            )

            # ---------------------------------
            # STEP 3
            # ---------------------------------

            print("")
            print(
                "3. Opening Department-wise Search..."
            )

            department_button = (
                find_department_search_button(
                    page
                )
            )

            if department_button is None:

                print("")
                print(
                    "ERROR: Department-wise Search "
                    "button could not be found."
                )

                print(
                    "Current page title:",
                    page.title()
                )

                print(
                    "Current URL:",
                    page.url
                )

                raise RuntimeError(
                    "Department-wise Search button "
                    "was not found."
                )

            print(
                "   Found button:",
                department_button.get_attribute(
                    "id"
                )
            )

            department_button.click()

            page.wait_for_load_state(
                "domcontentloaded",
                timeout=120000
            )

            time.sleep(3)

            print(
                "   Department search page:",
                page.url
            )

            # ---------------------------------
            # STEP 4
            # ---------------------------------

            print("")
            print(
                "4. Selecting Labour Department..."
            )

            department_dropdown = page.locator(
                "#ContentPlaceHolder1_ddlDepartment"
            )

            if department_dropdown.count() == 0:

                raise RuntimeError(
                    "Department dropdown not found."
                )

            department_dropdown.select_option(
                DEPARTMENT_VALUE
            )

            page.wait_for_load_state(
                "domcontentloaded",
                timeout=120000
            )

            time.sleep(3)

            print(
                "   Selected:",
                DEPARTMENT_NAME
            )

            # ---------------------------------
            # STEP 5
            # ---------------------------------

            print("")
            print(
                "5. Selecting Deputy Secretary Two..."
            )

            organization_dropdown = page.locator(
                "#ContentPlaceHolder1_ddlOrgName"
            )

            if organization_dropdown.count() == 0:

                raise RuntimeError(
                    "Organization dropdown not found."
                )

            # Wait until organization 2239 appears.

            for attempt in range(10):

                try:

                    option = organization_dropdown.locator(
                        f"option[value='{ORGANIZATION_VALUE}']"
                    )

                    if option.count() > 0:
                        break

                except Exception:
                    pass

                time.sleep(1)

            option = organization_dropdown.locator(
                f"option[value='{ORGANIZATION_VALUE}']"
            )

            if option.count() == 0:

                raise RuntimeError(
                    "Deputy Secretary Two was not "
                    "loaded into the organization dropdown."
                )

            organization_dropdown.select_option(
                ORGANIZATION_VALUE
            )

            print(
                "   Selected:",
                ORGANIZATION_NAME
            )

            # ---------------------------------
            # STEP 6
            # ---------------------------------

            print("")
            print(
                "6. Running search..."
            )

            search_button = page.locator(
                "#ContentPlaceHolder1_Button1"
            )

            if search_button.count() == 0:

                raise RuntimeError(
                    "Search button not found."
                )

            search_button.click()

            page.wait_for_load_state(
                "domcontentloaded",
                timeout=120000
            )

            time.sleep(4)

            print(
                "   Search completed."
            )

            # ---------------------------------
            # STEP 7
            # ---------------------------------

            print("")
            print(
                "7. Reading Gazette results..."
            )

            table = find_result_table(
                page
            )

            if table is None:

                raise RuntimeError(
                    "Gazette results table not found."
                )

            results = extract_result_metadata(
                table
            )

            print(
                "   Result rows found:",
                len(results)
            )

            if not results:

                raise RuntimeError(
                    "No Gazette results found."
                )

            # ---------------------------------
            # STEP 8
            # ---------------------------------

            print("")
            print(
                "8. Downloading Gazette PDFs..."
            )
            print("")

            successful = 0
            skipped = 0
            failed = 0

            for number, result in enumerate(
                results,
                start=1
            ):

                print(
                    f"--- Gazette {number}/{len(results)} ---"
                )

                print(
                    "Visible values:",
                    result["values"]
                )

                button_id = result[
                    "button_id"
                ]

                button = page.locator(
                    f"#{button_id}"
                )

                if button.count() == 0:

                    print(
                        "  PDF button not found."
                    )

                    failed += 1

                    continue

                try:

                    with page.expect_response(
                        lambda response:
                        response.request.method == "POST"
                        and "DepartmentWise_Search.aspx"
                        in response.url,
                        timeout=120000
                    ) as response_info:

                        # Use normal click first.
                        # This is the same control that
                        # we proved generates the POST.

                        button.click()

                    response = (
                        response_info.value
                    )

                    response_html = (
                        response.text()
                    )

                except Exception as error:

                    print(
                        "  PDF POST failed:",
                        error
                    )

                    failed += 1

                    continue

                pdf_path = extract_pdf_path(
                    response_html
                )

                if not pdf_path:

                    print(
                        "  Could not find PDF path "
                        "in server response."
                    )

                    failed += 1

                    continue

                pdf_url = normalize_pdf_url(
                    pdf_path
                )

                print(
                    "  PDF URL:",
                    pdf_url
                )

                match = re.search(
                    r"/WriteReadData/(\d{4})/(\d+)\.pdf",
                    pdf_url,
                    flags=re.IGNORECASE
                )

                if match:

                    year = match.group(
                        1
                    )

                    document_number = match.group(
                        2
                    )

                else:

                    year = str(
                        datetime.now().year
                    )

                    document_number = (
                        f"row_{number}"
                    )

                title = guess_title(
                    result["values"]
                )

                publication_date = guess_date(
                    result["values"]
                )

                update_type = guess_gazette_type(
                    result["values"]
                )

                base_name = safe_filename(
                    f"{year}_{document_number}_{title}"
                )

                pdf_filename = (
                    base_name
                    + ".pdf"
                )

                txt_filename = (
                    base_name
                    + ".txt"
                )

                json_filename = (
                    base_name
                    + ".json"
                )

                local_pdf = os.path.join(
                    PDF_DIR,
                    pdf_filename
                )

                local_txt = os.path.join(
                    TEXT_DIR,
                    txt_filename
                )

                local_json = os.path.join(
                    METADATA_DIR,
                    json_filename
                )

                if os.path.exists(
                    local_pdf
                ):

                    print(
                        "  Already downloaded."
                    )

                    skipped += 1

                    continue

                if not download_pdf(
                    context,
                    pdf_url,
                    local_pdf
                ):

                    failed += 1

                    continue

                print(
                    "  Extracting text..."
                )

                text = extract_pdf_text(
                    local_pdf
                )

                save_text(
                    text,
                    local_txt
                )

                metadata = {

                    "jurisdiction":
                        "Karnataka",

                    "department":
                        DEPARTMENT_NAME,

                    "organization":
                        ORGANIZATION_NAME,

                    "update_type":
                        update_type,

                    "title":
                        title,

                    "description":
                        "",

                    "publication_date":
                        publication_date,

                    "effective_date":
                        None,

                    "source":
                        "Karnataka e-Gazette",

                    "source_url":
                        HOME_URL,

                    "document_url":
                        pdf_url,

                    "pdf_path":
                        local_pdf,

                    "text_path":
                        local_txt,

                    "gazette_year":
                        year,

                    "document_number":
                        document_number,

                    "raw_values":
                        result["values"],

                    "collected_at":
                        datetime.now().isoformat(),
                }

                save_json(
                    metadata,
                    local_json
                )

                print(
                    "  Text saved."
                )

                print(
                    "  Metadata saved."
                )

                successful += 1

                time.sleep(
                    0.5
                )

            print("")
            print("========================================")
            print("             COLLECTION DONE")
            print("========================================")
            print(
                "Successful:",
                successful
            )
            print(
                "Skipped:",
                skipped
            )
            print(
                "Failed:",
                failed
            )
            print("")
            print(
                "PDF folder:",
                PDF_DIR
            )
            print(
                "Text folder:",
                TEXT_DIR
            )
            print(
                "Metadata folder:",
                METADATA_DIR
            )
            print("")

        finally:

            browser.close()


if __name__ == "__main__":
    collect()