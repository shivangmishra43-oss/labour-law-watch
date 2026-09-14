// ============================================
// LABOUR LAW WATCH
// Frontend application
// ============================================

let allUpdates = [];
let filteredUpdates = [];


// ============================================
// DOM ELEMENTS
// ============================================

const searchInput = document.getElementById("searchInput");

const jurisdictionButtons = document.querySelectorAll(
    "[data-jurisdiction]"
);

const typeFilters = document.getElementById(
    "typeFilters"
);

const sortSelect = document.getElementById(
    "sortSelect"
);

const updatesContainer = document.getElementById(
    "updatesContainer"
);

const loadingState = document.getElementById(
    "loadingState"
);

const errorState = document.getElementById(
    "errorState"
);

const errorMessage = document.getElementById(
    "errorMessage"
);

const emptyState = document.getElementById(
    "emptyState"
);

const resultsCount = document.getElementById(
    "resultsCount"
);

const totalUpdates = document.getElementById(
    "totalUpdates"
);

const karnatakaUpdates = document.getElementById(
    "karnatakaUpdates"
);

const centralUpdates = document.getElementById(
    "centralUpdates"
);

const latestDate = document.getElementById(
    "latestDate"
);

const detailModal = document.getElementById(
    "detailModal"
);

const modalClose = document.getElementById(
    "modalClose"
);

const modalBackdrop = detailModal
    ? detailModal.querySelector(".modal-backdrop")
    : null;

const modalSource = document.getElementById(
    "modalSource"
);

const modalTitle = document.getElementById(
    "modalTitle"
);

const modalMeta = document.getElementById(
    "modalMeta"
);

const modalContent = document.getElementById(
    "modalContent"
);

const modalSourceButton = document.getElementById(
    "modalSourceButton"
);

const modalDocumentButton = document.getElementById(
    "modalDocumentButton"
);


// ============================================
// CURRENT FILTER STATE
// ============================================

let currentJurisdiction = "all";
let currentType = "all";


// ============================================
// INITIALISE
// ============================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupEventListeners();

        loadUpdates();

    }
);


// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {

    // -----------------------------
    // SEARCH
    // -----------------------------

    if (searchInput) {

        searchInput.addEventListener(
            "input",
            () => {

                applyFilters();

            }
        );

    }


    // -----------------------------
    // JURISDICTION BUTTONS
    // -----------------------------

    jurisdictionButtons.forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    currentJurisdiction =
                        button.dataset.jurisdiction || "all";

                    jurisdictionButtons.forEach(
                        (item) => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );

                    button.classList.add(
                        "active"
                    );

                    applyFilters();

                }
            );

        }
    );


    // -----------------------------
    // SORT
    // -----------------------------

    if (sortSelect) {

        sortSelect.addEventListener(
            "change",
            () => {

                applyFilters();

            }
        );

    }


    // -----------------------------
    // MODAL CLOSE
    // -----------------------------

    if (modalClose) {

        modalClose.addEventListener(
            "click",
            closeModal
        );

    }


    if (modalBackdrop) {

        modalBackdrop.addEventListener(
            "click",
            closeModal
        );

    }


    // -----------------------------
    // ESCAPE KEY
    // -----------------------------

    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape" &&
                detailModal &&
                !detailModal.classList.contains("hidden")
            ) {

                closeModal();

            }

        }
    );

}


// ============================================
// LOAD UPDATES FROM FLASK
// ============================================

async function loadUpdates() {

    showLoading();

    try {

        const response = await fetch(
            "/api/updates",
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            }
        );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const data = await response.json();


        if (
            !data ||
            !Array.isArray(data.updates)
        ) {

            throw new Error(
                "Invalid API response"
            );

        }


        allUpdates = data.updates;

        filteredUpdates = [...allUpdates];


        buildDynamicTypeFilters();

        updateStats();

        applyFilters();


    } catch (error) {

        console.error(
            "Unable to load updates:",
            error
        );

        showError(
            "Unable to connect to the Flask backend. " +
            "Please make sure the server is running."
        );

    }

}


// ============================================
// BUILD UPDATE-TYPE FILTERS
// ============================================

function buildDynamicTypeFilters() {

    if (!typeFilters) {

        console.warn(
            "typeFilters element was not found."
        );

        return;

    }


    const types = [
        ...new Set(
            allUpdates
                .map(
                    (update) =>
                        update.update_type
                )
                .filter(
                    (type) =>
                        type &&
                        String(type).trim() !== ""
                )
                .map(
                    (type) =>
                        String(type).trim()
                )
        )
    ];


    types.sort(
        (a, b) =>
            a.localeCompare(
                b
            )
    );


    let html = `
        <button
            type="button"
            class="filter-button active"
            data-type="all"
        >
            All
        </button>
    `;


    types.forEach(
        (type) => {

            html += `
                <button
                    type="button"
                    class="filter-button"
                    data-type="${escapeAttribute(type)}"
                >
                    ${escapeHtml(type)}
                </button>
            `;

        }
    );


    typeFilters.innerHTML = html;


    const buttons =
        typeFilters.querySelectorAll(
            "[data-type]"
        );


    buttons.forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    currentType =
                        button.dataset.type || "all";


                    buttons.forEach(
                        (item) => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    button.classList.add(
                        "active"
                    );


                    applyFilters();

                }
            );

        }
    );

}


// ============================================
// APPLY FILTERS
// ============================================

function applyFilters() {

    const searchTerm =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";


    filteredUpdates =
        allUpdates.filter(
            (update) => {

                // -------------------------
                // JURISDICTION
                // -------------------------

                if (
                    currentJurisdiction !== "all" &&
                    String(
                        update.jurisdiction || ""
                    ).toLowerCase() !==
                    currentJurisdiction.toLowerCase()
                ) {

                    return false;

                }


                // -------------------------
                // UPDATE TYPE
                // -------------------------

                if (
                    currentType !== "all" &&
                    String(
                        update.update_type || ""
                    ).toLowerCase() !==
                    currentType.toLowerCase()
                ) {

                    return false;

                }


                // -------------------------
                // SEARCH
                // -------------------------

                if (searchTerm) {

                    const searchableText = [

                        update.title,

                        update.description,

                        update.topic,

                        update.source,

                        update.jurisdiction,

                        update.update_type

                    ]
                        .filter(
                            (value) =>
                                value !== null &&
                                value !== undefined
                        )
                        .join(" ")
                        .toLowerCase();


                    if (
                        !searchableText.includes(
                            searchTerm
                        )
                    ) {

                        return false;

                    }

                }


                return true;

            }
        );


    // -----------------------------
    // SORT
    // -----------------------------

    const sortOrder =
        sortSelect
            ? sortSelect.value
            : "newest";


    filteredUpdates.sort(
        (a, b) => {

            const dateA =
                parseDate(
                    a.publication_date
                );

            const dateB =
                parseDate(
                    b.publication_date
                );


            if (
                sortOrder === "oldest"
            ) {

                return dateA - dateB;

            }


            return dateB - dateA;

        }
    );


    renderUpdates();

}


// ============================================
// UPDATE STATS
// ============================================

function updateStats() {

    if (totalUpdates) {

        totalUpdates.textContent =
            allUpdates.length;

    }


    if (karnatakaUpdates) {

        karnatakaUpdates.textContent =
            allUpdates.filter(
                (update) =>
                    String(
                        update.jurisdiction || ""
                    ).toLowerCase() ===
                    "karnataka"
            ).length;

    }


    if (centralUpdates) {

        centralUpdates.textContent =
            allUpdates.filter(
                (update) =>
                    String(
                        update.jurisdiction || ""
                    ).toLowerCase() ===
                    "central"
            ).length;

    }


    if (latestDate) {

        const dates =
            allUpdates
                .map(
                    (update) =>
                        update.publication_date
                )
                .filter(Boolean)
                .map(parseDate)
                .filter(
                    (date) =>
                        !isNaN(date.getTime())
                );


        if (dates.length > 0) {

            const newest =
                new Date(
                    Math.max(
                        ...dates.map(
                            (date) =>
                                date.getTime()
                        )
                    )
                );


            latestDate.textContent =
                formatDate(
                    newest
                );

        } else {

            latestDate.textContent =
                "—";

        }

    }

}


// ============================================
// RENDER UPDATE CARDS
// ============================================

function renderUpdates() {

    hideLoading();

    hideError();


    if (resultsCount) {

        resultsCount.textContent =
            `${filteredUpdates.length} update${
                filteredUpdates.length === 1
                    ? ""
                    : "s"
            }`;

    }


    if (!updatesContainer) {

        console.error(
            "updatesContainer element not found."
        );

        return;

    }


    updatesContainer.innerHTML = "";


    if (
        filteredUpdates.length === 0
    ) {

        showEmpty();

        return;

    }


    hideEmpty();


    filteredUpdates.forEach(
        (update) => {

            updatesContainer.appendChild(
                createUpdateCard(
                    update
                )
            );

        }
    );

}


// ============================================
// CREATE UPDATE CARD
// ============================================

function createUpdateCard(
    update
) {

    const card =
        document.createElement(
            "article"
        );


    card.className =
        "update-card";


    const updateType =
        update.update_type ||
        "Update";


    const jurisdiction =
        update.jurisdiction ||
        "—";


    const title =
        update.title ||
        "Untitled update";


    const description =
        getShortDescription(
            update.description
        );


    const publicationDate =
        update.publication_date
            ? formatDate(
                update.publication_date
            )
            : "—";


    const effectiveDate =
        update.effective_date
            ? formatDate(
                update.effective_date
            )
            : null;


    const topic =
        update.topic ||
        "";


    card.innerHTML = `

        <div class="card-top">

            <div class="card-badges">

                <span class="badge badge-type">
                    ${escapeHtml(updateType)}
                </span>

                <span class="badge badge-jurisdiction">
                    ${escapeHtml(jurisdiction)}
                </span>

            </div>

        </div>


        <h2 class="card-title">
            ${escapeHtml(title)}
        </h2>


        <div class="card-dates">

            <div class="date-item">

                <span class="date-label">
                    Published
                </span>

                <span class="date-value">
                    ${escapeHtml(publicationDate)}
                </span>

            </div>

            ${
                effectiveDate
                    ? `
                        <div class="date-item">

                            <span class="date-label">
                                Effective
                            </span>

                            <span class="date-value">
                                ${escapeHtml(
                                    effectiveDate
                                )}
                            </span>

                        </div>
                    `
                    : ""
            }

        </div>


        ${
            description
                ? `
                    <p class="card-description">
                        ${escapeHtml(description)}
                    </p>
                `
                : ""
        }


        ${
            topic
                ? `
                    <div class="card-topic">
                        ${escapeHtml(topic)}
                    </div>
                `
                : ""
        }


        <div class="card-footer">

            <span class="card-source">
                ${escapeHtml(
                    update.source ||
                    "Official source"
                )}
            </span>


            <button
                type="button"
                class="view-button"
                data-update-id="${escapeAttribute(
                    update.id
                )}"
            >
                View update →
            </button>

        </div>

    `;


    const viewButton =
        card.querySelector(
            ".view-button"
        );


    if (viewButton) {

        viewButton.addEventListener(
            "click",
            () => {

                openModal(
                    update
                );

            }
        );

    }


    return card;

}


// ============================================
// MODAL
// ============================================

function openModal(
    update
) {

    if (!detailModal) {

        return;

    }


    if (modalSource) {

        modalSource.textContent =
            update.source ||
            "Official source";

    }


    if (modalTitle) {

        modalTitle.textContent =
            update.title ||
            "Untitled update";

    }


    if (modalMeta) {

        const metaParts = [];


        if (update.update_type) {

            metaParts.push(
                update.update_type
            );

        }


        if (update.jurisdiction) {

            metaParts.push(
                update.jurisdiction
            );

        }


        if (update.topic) {

            metaParts.push(
                update.topic
            );

        }


        modalMeta.textContent =
            metaParts.join(
                " • "
            );

    }


    if (modalContent) {

        modalContent.innerHTML =
            buildModalContent(
                update
            );

    }


    if (
        modalSourceButton
    ) {

        if (
            update.source_url
        ) {

            modalSourceButton.href =
                update.source_url;

            modalSourceButton.style.display =
                "inline-flex";

        } else {

            modalSourceButton.style.display =
                "none";

        }

    }


    if (
        modalDocumentButton
    ) {

        if (
            update.document_url
        ) {

            modalDocumentButton.href =
                update.document_url;

            modalDocumentButton.style.display =
                "inline-flex";

        } else {

            modalDocumentButton.style.display =
                "none";

        }

    }


    detailModal.classList.remove(
        "hidden"
    );


    detailModal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "modal-open"
    );

}


function closeModal() {

    if (!detailModal) {

        return;

    }


    detailModal.classList.add(
        "hidden"
    );


    detailModal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "modal-open"
    );

}


// ============================================
// MODAL CONTENT
// ============================================

function buildModalContent(
    update
) {

    let html = "";


    if (
        update.description
    ) {

        const sections =
            parseDescription(
                update.description
            );


        if (
            sections.summary
        ) {

            html += `
                <section class="detail-section">

                    <h3>
                        Summary
                    </h3>

                    <p>
                        ${escapeHtml(
                            sections.summary
                        )}
                    </p>

                </section>
            `;

        }


        if (
            sections.whatChanged
        ) {

            html += `
                <section class="detail-section">

                    <h3>
                        What changed
                    </h3>

                    <p>
                        ${escapeHtml(
                            sections.whatChanged
                        )}
                    </p>

                </section>
            `;

        }


        if (
            sections.provisions
        ) {

            html += `
                <section class="detail-section">

                    <h3>
                        Provisions
                    </h3>

                    <p>
                        ${escapeHtml(
                            sections.provisions
                        )}
                    </p>

                </section>
            `;

        }


        if (
            sections.affected
        ) {

            html += `
                <section class="detail-section">

                    <h3>
                        Who is affected
                    </h3>

                    <p>
                        ${escapeHtml(
                            sections.affected
                        )}
                    </p>

                </section>
            `;

        }


        if (
            sections.action
        ) {

            html += `
                <section class="detail-section">

                    <h3>
                        Action required
                    </h3>

                    <p>
                        ${escapeHtml(
                            sections.action
                        )}
                    </p>

                </section>
            `;

        }

    }


    // -----------------------------
    // DATES
    // -----------------------------

    html += `

        <section class="detail-section">

            <h3>
                Key dates
            </h3>

            <div class="detail-grid">

                <div class="detail-item">

                    <span>
                        Publication date
                    </span>

                    <strong>
                        ${
                            update.publication_date
                                ? escapeHtml(
                                    formatDate(
                                        update.publication_date
                                    )
                                )
                                : "—"
                        }
                    </strong>

                </div>


                <div class="detail-item">

                    <span>
                        Effective date
                    </span>

                    <strong>
                        ${
                            update.effective_date
                                ? escapeHtml(
                                    formatDate(
                                        update.effective_date
                                    )
                                )
                                : "—"
                        }
                    </strong>

                </div>

            </div>

        </section>

    `;


    if (
        update.topic
    ) {

        html += `

            <section class="detail-section">

                <h3>
                    Topic
                </h3>

                <p>
                    ${escapeHtml(
                        update.topic
                    )}
                </p>

            </section>

        `;

    }


    if (!html.trim()) {

        html = `
            <p>
                No additional summary is available
                for this update.
            </p>
        `;

    }


    return html;

}


// ============================================
// DESCRIPTION PARSER
// ============================================

function parseDescription(
    description
) {

    const result = {

        summary: "",

        whatChanged: "",

        provisions: "",

        affected: "",

        action: ""

    };


    if (
        !description
    ) {

        return result;

    }


    const text =
        String(
            description
        );


    // Try to detect common headings.

    const patterns = [

        {
            key: "summary",
            names: [
                "Summary",
                "SUMMARY"
            ]
        },

        {
            key: "whatChanged",
            names: [
                "What changed",
                "WHAT CHANGED"
            ]
        },

        {
            key: "provisions",
            names: [
                "Provisions",
                "PROVISIONS"
            ]
        },

        {
            key: "affected",
            names: [
                "Who is affected",
                "WHO IS AFFECTED"
            ]
        },

        {
            key: "action",
            names: [
                "Action required",
                "ACTION REQUIRED"
            ]
        }

    ];


    let foundHeading =
        false;


    patterns.forEach(
        (pattern) => {

            pattern.names.forEach(
                (heading) => {

                    if (
                        text.includes(
                            heading + ":"
                        )
                    ) {

                        foundHeading = true;

                    }

                }
            );

        }
    );


    if (!foundHeading) {

        result.summary =
            text.trim();

        return result;

    }


    // Basic heading-based extraction.

    const headingRegex =
        /(Summary|What changed|Provisions|Who is affected|Action required)\s*:/gi;


    const matches = [
        ...text.matchAll(
            headingRegex
        )
    ];


    matches.forEach(
        (
            match,
            index
        ) => {

            const heading =
                match[1]
                    .toLowerCase();


            const start =
                match.index +
                match[0].length;


            const end =
                index + 1 <
                matches.length
                    ? matches[
                        index + 1
                    ].index
                    : text.length;


            const value =
                text
                    .slice(
                        start,
                        end
                    )
                    .trim();


            if (
                heading ===
                "summary"
            ) {

                result.summary =
                    value;

            }


            if (
                heading ===
                "what changed"
            ) {

                result.whatChanged =
                    value;

            }


            if (
                heading ===
                "provisions"
            ) {

                result.provisions =
                    value;

            }


            if (
                heading ===
                "who is affected"
            ) {

                result.affected =
                    value;

            }


            if (
                heading ===
                "action required"
            ) {

                result.action =
                    value;

            }

        }
    );


    return result;

}


// ============================================
// SHORT DESCRIPTION
// ============================================

function getShortDescription(
    description
) {

    if (
        !description
    ) {

        return "";

    }


    const text =
        String(
            description
        ).trim();


    if (
        text.length <= 220
    ) {

        return text;

    }


    return (
        text.substring(
            0,
            220
        ).trim() +
        "..."
    );

}


// ============================================
// LOADING / ERROR / EMPTY STATES
// ============================================

function showLoading() {

    if (loadingState) {

        loadingState.classList.remove(
            "hidden"
        );

    }


    hideError();

}


function hideLoading() {

    if (loadingState) {

        loadingState.classList.add(
            "hidden"
        );

    }

}


function showError(
    message
) {

    hideLoading();

    hideEmpty();


    if (errorState) {

        errorState.classList.remove(
            "hidden"
        );

    }


    if (errorMessage) {

        errorMessage.textContent =
            message;

    }

}


function hideError() {

    if (errorState) {

        errorState.classList.add(
            "hidden"
        );

    }

}


function showEmpty() {

    if (emptyState) {

        emptyState.classList.remove(
            "hidden"
        );

    }

}


function hideEmpty() {

    if (emptyState) {

        emptyState.classList.add(
            "hidden"
        );

    }

}


// ============================================
// DATE HELPERS
// ============================================

function parseDate(
    value
) {

    if (!value) {

        return new Date(
            "invalid"
        );

    }


    const text =
        String(
            value
        ).trim();


    // YYYY-MM-DD

    if (
        /^\d{4}-\d{2}-\d{2}$/.test(
            text
        )
    ) {

        const [
            year,
            month,
            day
        ] =
            text
                .split("-")
                .map(Number);


        return new Date(
            year,
            month - 1,
            day
        );

    }


    return new Date(
        text
    );

}


function formatDate(
    value
) {

    const date =
        value instanceof Date
            ? value
            : parseDate(value);


    if (
        isNaN(
            date.getTime()
        )
    ) {

        return "—";

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
// HTML ESCAPING
// ============================================

function escapeHtml(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(
        value
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


function escapeAttribute(
    value
) {

    return escapeHtml(
        value
    );

}