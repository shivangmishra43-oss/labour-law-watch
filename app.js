// ============================================
// LABOUR LAW WATCH
// FRONTEND JAVASCRIPT
// ============================================


// ============================================
// GLOBAL DATA
// ============================================

let allUpdates = [];


// ============================================
// DOM ELEMENTS
// ============================================

const updatesContainer =
    document.getElementById("updatesContainer");

const searchInput =
    document.getElementById("searchInput");

const jurisdictionFilter =
    document.getElementById("jurisdictionFilter");

const typeFilter =
    document.getElementById("typeFilter");

const resultsCount =
    document.getElementById("resultsCount");

const totalUpdates =
    document.getElementById("totalUpdates");

const karnatakaUpdates =
    document.getElementById("karnatakaUpdates");

const centralUpdates =
    document.getElementById("centralUpdates");

const latestDate =
    document.getElementById("latestDate");

const detailModal =
    document.getElementById("detailModal");

const modalBody =
    document.getElementById("modalBody");

const closeModal =
    document.getElementById("closeModal");


// ============================================
// LOAD DATA
// ============================================

async function loadUpdates() {

    try {

        /*
         * IMPORTANT:
         *
         * This is intentionally a relative path.
         *
         * It works both locally:
         *
         * http://localhost:8000/data/updates.json
         *
         * and on GitHub Pages:
         *
         * /labour-law-watch/data/updates.json
         */

        const response =
            await fetch("data/updates.json", {
                cache: "no-store"
            });


        if (!response.ok) {

            throw new Error(
                `Could not load updates.json (${response.status})`
            );

        }


        const data =
            await response.json();


        if (
            !data ||
            !Array.isArray(data.updates)
        ) {

            throw new Error(
                "Invalid updates.json format."
            );

        }


        allUpdates =
            data.updates;


        populateTypeFilter();

        updateStatistics();

        renderUpdates();


    } catch (error) {

        console.error(
            "Error loading updates:",
            error
        );


        updatesContainer.innerHTML = `

            <div class="empty-state">

                <h3>
                    Unable to load updates
                </h3>

                <p>
                    Please check whether
                    data/updates.json is available.
                </p>

            </div>

        `;

    }

}


// ============================================
// POPULATE UPDATE TYPE FILTER
// ============================================

function populateTypeFilter() {

    if (!typeFilter) {
        return;
    }


    const types = [
        ...new Set(
            allUpdates
                .map(update => update.update_type)
                .filter(type => type)
                .map(type => String(type).trim())
        )
    ];


    types.sort(
        (a, b) =>
            a.localeCompare(b)
    );


    typeFilter.innerHTML = `

        <option value="all">
            All
        </option>

    `;


    types.forEach(type => {

        const option =
            document.createElement("option");

        option.value = type;

        option.textContent = type;

        typeFilter.appendChild(option);

    });

}


// ============================================
// UPDATE STATISTICS
// ============================================

function updateStatistics() {

    const total =
        allUpdates.length;


    const karnataka =
        allUpdates.filter(
            update =>
                String(update.jurisdiction)
                    .toLowerCase()
                    === "karnataka"
        ).length;


    const central =
        allUpdates.filter(
            update =>
                String(update.jurisdiction)
                    .toLowerCase()
                    === "central"
        ).length;


    if (totalUpdates) {

        totalUpdates.textContent =
            total;

    }


    if (karnatakaUpdates) {

        karnatakaUpdates.textContent =
            karnataka;

    }


    if (centralUpdates) {

        centralUpdates.textContent =
            central;

    }


    if (
        latestDate &&
        allUpdates.length > 0
    ) {

        const dates =
            allUpdates
                .map(update => update.publication_date)
                .filter(date => date)
                .sort()
                .reverse();


        if (dates.length > 0) {

            latestDate.textContent =
                formatDate(dates[0]);

        }

    }

}


// ============================================
// FILTER UPDATES
// ============================================

function getFilteredUpdates() {

    const searchTerm =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";


    const jurisdiction =
        jurisdictionFilter
            ? jurisdictionFilter.value
            : "all";


    const type =
        typeFilter
            ? typeFilter.value
            : "all";


    return allUpdates.filter(update => {

        // ------------------------------------
        // SEARCH
        // ------------------------------------

        const searchableText = [

            update.title,

            update.description,

            update.topic,

            update.update_type,

            update.jurisdiction,

            update.source

        ]
            .filter(value => value)
            .join(" ")
            .toLowerCase();


        if (
            searchTerm &&
            !searchableText.includes(searchTerm)
        ) {

            return false;

        }


        // ------------------------------------
        // JURISDICTION
        // ------------------------------------

        if (
            jurisdiction !== "all" &&
            update.jurisdiction !== jurisdiction
        ) {

            return false;

        }


        // ------------------------------------
        // UPDATE TYPE
        // ------------------------------------

        if (
            type !== "all" &&
            update.update_type !== type
        ) {

            return false;

        }


        return true;

    });

}


// ============================================
// RENDER UPDATES
// ============================================

function renderUpdates() {

    const filteredUpdates =
        getFilteredUpdates();


    if (resultsCount) {

        resultsCount.textContent =
            `${filteredUpdates.length} ${
                filteredUpdates.length === 1
                    ? "update"
                    : "updates"
            }`;

    }


    if (
        !updatesContainer
    ) {

        return;

    }


    if (
        filteredUpdates.length === 0
    ) {

        updatesContainer.innerHTML = `

            <div class="empty-state">

                <h3>
                    No updates found
                </h3>

                <p>
                    Try changing your search
                    or filters.
                </p>

            </div>

        `;

        return;

    }


    updatesContainer.innerHTML =
        filteredUpdates
            .map(update => createUpdateCard(update))
            .join("");


    attachCardListeners();

}


// ============================================
// CREATE UPDATE CARD
// ============================================

function createUpdateCard(update) {

    const title =
        escapeHtml(
            update.title || "Untitled update"
        );


    const description =
        escapeHtml(
            update.description ||
            "No summary available."
        );


    const jurisdiction =
        escapeHtml(
            update.jurisdiction || "—"
        );


    const type =
        escapeHtml(
            update.update_type || "Update"
        );


    const topic =
        escapeHtml(
            update.topic || "Labour Law"
        );


    const publicationDate =
        update.publication_date
            ? formatDate(update.publication_date)
            : "—";


    return `

        <article
            class="update-card"
            data-id="${escapeHtml(
                String(update.id ?? "")
            )}"
        >

            <div class="card-top">

                <span class="jurisdiction-badge">
                    ${jurisdiction}
                </span>

                <span class="date">
                    ${publicationDate}
                </span>

            </div>


            <h3 class="card-title">
                ${title}
            </h3>


            <p class="card-description">
                ${description}
            </p>


            <div class="card-meta">

                <span>
                    ${type}
                </span>

                <span>
                    ${topic}
                </span>

            </div>


            <button
                class="read-more"
                type="button"
                data-id="${escapeHtml(
                    String(update.id ?? "")
                )}"
            >
                View update
                <span>→</span>
            </button>

        </article>

    `;

}


// ============================================
// ATTACH CARD LISTENERS
// ============================================

function attachCardListeners() {

    const buttons =
        document.querySelectorAll(
            ".read-more"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const id =
                    button.dataset.id;

                openUpdateModal(id);

            }
        );

    });


    const cards =
        document.querySelectorAll(
            ".update-card"
        );


    cards.forEach(card => {

        card.addEventListener(
            "click",
            event => {

                if (
                    event.target.closest(
                        ".read-more"
                    )
                ) {

                    return;

                }


                const id =
                    card.dataset.id;

                openUpdateModal(id);

            }
        );

    });

}


// ============================================
// OPEN DETAIL MODAL
// ============================================

function openUpdateModal(id) {

    const update =
        allUpdates.find(
            item =>
                String(item.id) === String(id)
        );


    if (!update) {

        return;

    }


    const title =
        escapeHtml(
            update.title || "Untitled update"
        );


    const description =
        escapeHtml(
            update.description ||
            "No summary available."
        );


    const jurisdiction =
        escapeHtml(
            update.jurisdiction || "—"
        );


    const type =
        escapeHtml(
            update.update_type || "—"
        );


    const topic =
        escapeHtml(
            update.topic || "—"
        );


    const source =
        escapeHtml(
            update.source || "—"
        );


    const publicationDate =
        update.publication_date
            ? formatDate(update.publication_date)
            : "—";


    const effectiveDate =
        update.effective_date
            ? formatDate(update.effective_date)
            : "—";


    const sourceUrl =
        safeUrl(update.source_url);


    const documentUrl =
        safeUrl(update.document_url);


    modalBody.innerHTML = `

        <div class="modal-header">

            <span class="jurisdiction-badge">
                ${jurisdiction}
            </span>

            <span class="date">
                ${publicationDate}
            </span>

        </div>


        <h2 class="modal-title">
            ${title}
        </h2>


        <div class="modal-details">

            <div class="detail-item">

                <span class="detail-label">
                    Source
                </span>

                <span class="detail-value">
                    ${source}
                </span>

            </div>


            <div class="detail-item">

                <span class="detail-label">
                    Update Type
                </span>

                <span class="detail-value">
                    ${type}
                </span>

            </div>


            <div class="detail-item">

                <span class="detail-label">
                    Topic
                </span>

                <span class="detail-value">
                    ${topic}
                </span>

            </div>


            <div class="detail-item">

                <span class="detail-label">
                    Publication Date
                </span>

                <span class="detail-value">
                    ${publicationDate}
                </span>

            </div>


            <div class="detail-item">

                <span class="detail-label">
                    Effective Date
                </span>

                <span class="detail-value">
                    ${effectiveDate}
                </span>

            </div>

        </div>


        <section class="modal-section">

            <h3>
                Summary
            </h3>

            <p>
                ${description}
            </p>

        </section>


        <div class="modal-actions">

            ${
                sourceUrl
                    ? `
                        <a
                            href="${sourceUrl}"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="source-button"
                        >
                            Source Website
                        </a>
                    `
                    : ""
            }


            ${
                documentUrl
                    ? `
                        <a
                            href="${documentUrl}"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="source-button primary"
                        >
                            View Gazette
                        </a>
                    `
                    : ""
            }

        </div>

    `;


    detailModal.classList.remove(
        "hidden"
    );


    document.body.classList.add(
        "modal-open"
    );

}


// ============================================
// CLOSE MODAL
// ============================================

function closeDetailModal() {

    if (!detailModal) {

        return;

    }


    detailModal.classList.add(
        "hidden"
    );


    document.body.classList.remove(
        "modal-open"
    );

}


// ============================================
// EVENT LISTENERS
// ============================================

if (searchInput) {

    searchInput.addEventListener(
        "input",
        renderUpdates
    );

}


if (jurisdictionFilter) {

    jurisdictionFilter.addEventListener(
        "change",
        renderUpdates
    );

}


if (typeFilter) {

    typeFilter.addEventListener(
        "change",
        renderUpdates
    );

}


if (closeModal) {

    closeModal.addEventListener(
        "click",
        closeDetailModal
    );

}


if (detailModal) {

    const overlay =
        detailModal.querySelector(
            ".modal-overlay"
        );


    if (overlay) {

        overlay.addEventListener(
            "click",
            closeDetailModal
        );

    }

}


// ============================================
// ESCAPE KEY
// ============================================

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape"
        ) {

            closeDetailModal();

        }

    }
);


// ============================================
// DATE FORMATTING
// ============================================

function formatDate(dateString) {

    if (!dateString) {

        return "—";

    }


    const date =
        new Date(dateString);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return escapeHtml(
            String(dateString)
        );

    }


    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );

}


// ============================================
// URL SAFETY
// ============================================

function safeUrl(url) {

    if (!url) {

        return "";

    }


    try {

        const parsed =
            new URL(url);


        if (
            parsed.protocol !== "http:" &&
            parsed.protocol !== "https:"
        ) {

            return "";

        }


        return escapeHtml(
            parsed.href
        );

    } catch {

        return "";

    }

}


// ============================================
// HTML ESCAPING
// ============================================

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


// ============================================
// START APPLICATION
// ============================================

loadUpdates();