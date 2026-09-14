from playwright.sync_api import sync_playwright
import os


URL = "https://erajyapatra.karnataka.gov.in/"


def main():

    print("")
    print("=" * 80)
    print("KARNATAKA E-GAZETTE")
    print("PDF RESPONSE INVESTIGATION")
    print("=" * 80)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context(
            ignore_https_errors=True,
            accept_downloads=True
        )

        page = context.new_page()

        # =====================================================
        # 1. OPEN WEBSITE
        # =====================================================

        print("")
        print("1. Opening Karnataka e-Gazette...")

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(3000)

        # =====================================================
        # 2. GAZETTE SEARCH
        # =====================================================

        print(
            "2. Opening Gazette Search..."
        )

        page.locator(
            "a[href*=\"__doPostBack('sgzt','')\"]"
        ).first.click()

        page.wait_for_timeout(4000)

        # =====================================================
        # 3. DEPARTMENT-WISE SEARCH
        # =====================================================

        print(
            "3. Opening Department-wise Search..."
        )

        page.locator(
            "#ContentPlaceHolder1_Button2"
        ).click()

        page.wait_for_timeout(5000)

        # =====================================================
        # 4. LABOUR DEPARTMENT
        # =====================================================

        print(
            "4. Selecting Labour Department..."
        )

        department = page.locator(
            "#ContentPlaceHolder1_ddlDepartment"
        )

        labour = department.locator(
            "option"
        ).filter(
            has_text="Labour Department"
        ).first

        department.select_option(
            value="1340"
        )

        page.wait_for_timeout(
            8000
        )

        # =====================================================
        # 5. ORGANIZATION
        # =====================================================

        print(
            "5. Selecting Deputy Secretary Two..."
        )

        organization = page.locator(
            "#ContentPlaceHolder1_ddlOrgName"
        )

        deputy = organization.locator(
            "option"
        ).filter(
            has_text="DEPUTY SECRETARY TWO"
        ).first

        organization.select_option(
            value="2239"
        )

        page.wait_for_timeout(
            1000
        )

        # =====================================================
        # 6. VERIFY
        # =====================================================

        print("")
        print("=" * 80)
        print("FILTERS")
        print("=" * 80)

        print(
            "Department:",
            department.input_value()
        )

        print(
            "Organization:",
            organization.input_value()
        )

        if (
            department.input_value()
            != "1340"
        ):

            print(
                "ERROR: Department incorrect."
            )

            browser.close()
            return

        if (
            organization.input_value()
            != "2239"
        ):

            print(
                "ERROR: Organization incorrect."
            )

            browser.close()
            return

        # =====================================================
        # 7. SEARCH
        # =====================================================

        print("")
        print(
            "6. Running search..."
        )

        page.locator(
            "#ContentPlaceHolder1_Button1"
        ).click()

        page.wait_for_timeout(
            10000
        )

        print(
            "Search complete."
        )

        # =====================================================
        # 8. FIND PDF BUTTONS
        # =====================================================

        pdf_buttons = page.locator(
            "input[type='image'][src*='pdf_icon']"
        )

        count = pdf_buttons.count()

        print("")
        print("=" * 80)
        print("PDF BUTTONS")
        print("=" * 80)

        print(
            "PDF buttons:",
            count
        )

        if count == 0:

            print(
                "ERROR: No PDF buttons."
            )

            browser.close()
            return

        # =====================================================
        # 9. FIRST BUTTON
        # =====================================================

        first_pdf = pdf_buttons.first

        print("")
        print(
            "FIRST PDF BUTTON"
        )

        print(
            "ID:",
            first_pdf.get_attribute("id")
        )

        print(
            "NAME:",
            first_pdf.get_attribute("name")
        )

        print(
            "ONCLICK:",
            first_pdf.get_attribute(
                "onclick"
            )
        )

        # =====================================================
        # 10. READ FIRST RESULT
        # =====================================================

        try:

            row = first_pdf.locator(
                "xpath=ancestor::tr[1]"
            )

            print("")
            print(
                "FIRST RESULT TEXT:"
            )

            print(
                row.inner_text()
            )

        except Exception as e:

            print(
                "Could not read row:",
                e
            )

        # =====================================================
        # 11. RESPONSE CAPTURE
        # =====================================================

        print("")
        print("=" * 80)
        print("CLICKING PDF AND CAPTURING POST RESPONSE")
        print("=" * 80)

        captured_response = None

        def response_handler(response):

            nonlocal captured_response

            if (
                response.request.method
                == "POST"
                and
                "DepartmentWise_Search.aspx"
                in response.url
            ):

                captured_response = response

                print("")
                print(
                    ">>> PDF POST RESPONSE CAPTURED"
                )

                print(
                    "STATUS:",
                    response.status
                )

                print(
                    "URL:",
                    response.url
                )

                print(
                    "CONTENT TYPE:",
                    response.headers.get(
                        "content-type",
                        ""
                    )
                )

        page.on(
            "response",
            response_handler
        )

        # =====================================================
        # 12. CLICK WITH MOUSE
        # =====================================================

        box = first_pdf.bounding_box()

        if not box:

            print(
                "ERROR: PDF button has no position."
            )

            browser.close()
            return

        print("")
        print(
            "Clicking PDF..."
        )

        page.mouse.move(
            box["x"] +
            box["width"] / 2,

            box["y"] +
            box["height"] / 2
        )

        page.wait_for_timeout(
            500
        )

        page.mouse.down()

        page.wait_for_timeout(
            200
        )

        page.mouse.up()

        # =====================================================
        # 13. WAIT
        # =====================================================

        print("")
        print(
            "Waiting for POST response..."
        )

        page.wait_for_timeout(
            8000
        )

        # =====================================================
        # 14. READ RESPONSE
        # =====================================================

        if captured_response is None:

            print("")
            print(
                "ERROR: POST response not captured."
            )

        else:

            print("")
            print("=" * 80)
            print("READING POST RESPONSE")
            print("=" * 80)

            try:

                body = (
                    captured_response
                    .body()
                )

                print(
                    "Response bytes:",
                    len(body)
                )

                # Save exact response
                # as returned by server.

                response_path = (
                    "downloads/"
                    "karnataka_pdf_post_response.html"
                )

                os.makedirs(
                    "downloads/karnataka",
                    exist_ok=True
                )

                with open(
                    response_path,
                    "wb"
                ) as f:

                    f.write(
                        body
                    )

                print("")
                print(
                    "Raw response saved:"
                )

                print(
                    response_path
                )

                # =================================================
                # DECODE
                # =================================================

                text = body.decode(
                    "utf-8",
                    errors="replace"
                )

                # =================================================
                # SEARCH IMPORTANT TERMS
                # =================================================

                terms = [
                    "pdf",
                    "WriteReadData",
                    "ViewPDF",
                    "window.open",
                    "document",
                    "download",
                    "error",
                    "File",
                    "Gazette"
                ]

                print("")
                print("=" * 80)
                print("IMPORTANT TERMS FOUND")
                print("=" * 80)

                lower_text = text.lower()

                for term in terms:

                    occurrences = (
                        lower_text.count(
                            term.lower()
                        )
                    )

                    print(
                        term,
                        "->",
                        occurrences
                    )

                # =================================================
                # SHOW LINES CONTAINING PDF
                # =================================================

                print("")
                print("=" * 80)
                print("LINES CONTAINING PDF / DOCUMENT")
                print("=" * 80)

                lines = text.splitlines()

                shown = 0

                for line_number, line in enumerate(
                    lines,
                    start=1
                ):

                    lower_line = line.lower()

                    if (
                        "pdf"
                        in lower_line
                        or
                        "writereaddata"
                        in lower_line
                        or
                        "viewpdf"
                        in lower_line
                        or
                        "download"
                        in lower_line
                        or
                        "document"
                        in lower_line
                    ):

                        print("")
                        print(
                            f"LINE {line_number}:"
                        )

                        # Limit very long lines.

                        if len(line) > 2000:

                            print(
                                line[:2000]
                            )

                            print(
                                "[LINE TRUNCATED]"
                            )

                        else:

                            print(
                                line
                            )

                        shown += 1

                        if shown >= 30:

                            print("")
                            print(
                                "[Only first 30 "
                                "matching lines shown]"
                            )

                            break

                if shown == 0:

                    print(
                        "No relevant lines found."
                    )

                # =================================================
                # SEARCH FOR HTTP URLS
                # =================================================

                print("")
                print("=" * 80)
                print("POSSIBLE URLS")
                print("=" * 80)

                import re

                urls = re.findall(
                    r'https?://[^"\'<>\s]+',
                    text
                )

                unique_urls = []

                for url in urls:

                    if url not in unique_urls:

                        unique_urls.append(
                            url
                        )

                if unique_urls:

                    for url in unique_urls[:50]:

                        print(
                            url
                        )

                else:

                    print(
                        "No absolute URLs found."
                    )

            except Exception as e:

                print("")
                print(
                    "ERROR READING RESPONSE:"
                )

                print(
                    e
                )

        # =====================================================
        # 15. FINAL PAGE
        # =====================================================

        print("")
        print("=" * 80)
        print("FINAL PAGE")
        print("=" * 80)

        print(
            "URL:",
            page.url
        )

        print(
            "Title:",
            page.title()
        )

        # =====================================================
        # 16. SAVE CURRENT PAGE
        # =====================================================

        current_path = (
            "downloads/"
            "karnataka_after_pdf_response.html"
        )

        with open(
            current_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                page.content()
            )

        print("")
        print(
            "Current page saved:"
        )

        print(
            current_path
        )

        # =====================================================
        # 17. FINISH
        # =====================================================

        print("")
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

        print("")
        print(
            "Browser remains open for 5 minutes."
        )

        page.wait_for_timeout(
            300000
        )

        browser.close()


if __name__ == "__main__":
    main()