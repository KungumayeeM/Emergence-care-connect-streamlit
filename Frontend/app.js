// ============================================================
// EMERGENCYCARE CONNECT
// MAIN DASHBOARD JAVASCRIPT
// ============================================================


// ============================================================
// AUTHENTICATION
// ============================================================

const currentUser = protectDashboard();


// ============================================================
// SELECTED RESERVATION
// ============================================================

let selected = null;


// ============================================================
// API HELPER
// ============================================================

async function api(
    url,
    options = {}
) {

    const response = await fetch(
        url,
        {
            headers: {
                "Content-Type":
                    "application/json",

                ...(options.headers || {})
            },

            ...options
        }
    );


    let data;

    try {

        data =
            await response.json();

    } catch {

        throw new Error(
            "Unable to connect to the server."
        );

    }


    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Request failed."
        );

    }


    return data;
}


// ============================================================
// USER INFORMATION
// ============================================================

function loadUserInformation() {

    if (!currentUser) return;


    const userName =
        document.getElementById(
            "userName"
        );


    const userRole =
        document.getElementById(
            "userRole"
        );


    const userAvatar =
        document.getElementById(
            "userAvatar"
        );


    userName.textContent =
        currentUser.full_name;


    userRole.textContent =
        formatRole(currentUser.role);


    userAvatar.textContent =
        currentUser.full_name
            .charAt(0)
            .toUpperCase();
}


function formatRole(role) {

    if (!role) return "User";

    return role
        .toLowerCase()
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );
}


// ============================================================
// DASHBOARD SUMMARY
// ============================================================

async function loadSummary() {

    try {

        const data =
            await api(
                "/dashboard/summary"
            );


        const summary =
            data.summary;


        setText(
            "hospitalCount",
            summary.hospital_count
        );


        setText(
            "icuCount",
            summary.icu_available
        );


        setText(
            "ventilatorCount",
            summary.ventilators_available
        );


        setText(
            "bedCount",
            summary.emergency_beds_available
        );


        setText(
            "ambulanceCount",
            summary.active_ambulances
        );


        setText(
            "reservationCount",
            summary.active_reservations
        );


    } catch (error) {

        console.error(
            "Summary error:",
            error
        );

    }
}


function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value ?? 0;
    }
}


// ============================================================
// GPS
// ============================================================

function useGPS() {

    const gpsMessage =
        document.getElementById(
            "gps"
        );


    if (!navigator.geolocation) {

        gpsMessage.textContent =
            "GPS is not supported by this browser.";

        gpsMessage.className =
            "gps-message error";

        return;
    }


    gpsMessage.textContent =
        "Requesting your location...";


    navigator.geolocation.getCurrentPosition(

        function(position) {

            document.getElementById(
                "lat"
            ).value =
                position.coords.latitude.toFixed(6);


            document.getElementById(
                "lon"
            ).value =
                position.coords.longitude.toFixed(6);


            gpsMessage.textContent =
                "✓ Current GPS location captured successfully.";


            gpsMessage.className =
                "gps-message success";

        },


        function(error) {

            console.error(
                "GPS error:",
                error
            );


            gpsMessage.textContent =
                "Unable to access GPS. Please allow location permission.";

            gpsMessage.className =
                "gps-message error";

        }

    );
}


// ============================================================
// GET RESOURCES
// ============================================================

function getSelectedResources() {

    return [
        ...document.querySelectorAll(
            ".resource-option input:checked"
        )
    ].map(
        checkbox =>
            checkbox.value
    );
}


// ============================================================
// MATCH HOSPITALS
// ============================================================

async function match() {

    const resultsContainer =
        document.getElementById(
            "results"
        );


    const name =
        document.getElementById(
            "name"
        ).value.trim();


    const emergency =
        document.getElementById(
            "emergency"
        ).value;


    const severity =
        document.getElementById(
            "severity"
        ).value;


    const latitude =
        parseFloat(
            document.getElementById(
                "lat"
            ).value
        );


    const longitude =
        parseFloat(
            document.getElementById(
                "lon"
            ).value
        );


    const resources =
        getSelectedResources();


    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    if (
        Number.isNaN(latitude) ||
        Number.isNaN(longitude)
    ) {

        showResultsError(
            "Please enter a valid latitude and longitude."
        );

        return;
    }


    if (resources.length === 0) {

        showResultsError(
            "Please select at least one required resource."
        );

        return;
    }


    // --------------------------------------------------------
    // LOADING
    // --------------------------------------------------------

    resultsContainer.innerHTML = `

        <div class="loading-state">

            <div class="large-spinner"></div>

            <h4>
                AI is analyzing hospitals...
            </h4>

            <p>
                Comparing emergency resources,
                distance, capacity and availability.
            </p>

        </div>

    `;


    try {

        const body = {

            name:
                name || "Emergency Patient",

            emergency_type:
                emergency,

            severity:
                severity,

            required_resources:
                resources,

            latitude:
                latitude,

            longitude:
                longitude

        };


        const data =
            await api(
                "/match-hospitals",
                {
                    method: "POST",

                    body:
                        JSON.stringify(body)
                }
            );


        selected =
            data.recommended_hospital;


        renderHospitalResults(
            data.ranked_hospitals || []
        );


        loadSummary();


    } catch (error) {

        showResultsError(
            error.message
        );

    }
}


// ============================================================
// DISPLAY HOSPITAL RESULTS
// ============================================================

function renderHospitalResults(
    hospitals
) {

    const container =
        document.getElementById(
            "results"
        );


    if (
        !hospitals ||
        hospitals.length === 0
    ) {

        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    ⚠️
                </div>

                <h4>
                    No hospitals found
                </h4>

                <p>
                    No matching hospitals were returned
                    for the selected requirements.
                </p>

            </div>

        `;

        return;
    }


    container.innerHTML =
        hospitals
            .map(
                (hospital, index) =>
                    hospitalCard(
                        hospital,
                        index
                    )
            )
            .join("");
}


// ============================================================
// HOSPITAL CARD
// ============================================================

function hospitalCard(
    hospital,
    index
) {

    const eligible =
        hospital.eligible;


    const suitability =
        hospital.suitability_score ?? 0;


    const unavailable =
        hospital.unavailable_requirements || [];


    const reasons =
        hospital.reasons || [];


    const rankClass =
        index === 0
            ? "top-ranked"
            : "";


    return `

        <div
            class="hospital-card
            ${eligible ? "eligible" : "not-eligible"}
            ${rankClass}"
        >


            ${
                index === 0
                    ? `
                        <div class="recommended-label">
                            ⭐ AI RECOMMENDED
                        </div>
                    `
                    : ""
            }


            <div class="hospital-main">


                <div class="hospital-number">
                    #${index + 1}
                </div>


                <div class="hospital-information">

                    <h4>
                        ${escapeHTML(
                            hospital.hospital_name
                        )}
                    </h4>


                    <p class="hospital-type">
                        ${escapeHTML(
                            hospital.hospital_type ||
                            "Healthcare Facility"
                        )}
                    </p>


                    <div class="hospital-meta">

                        <span>
                            📍
                            ${hospital.distance_km}
                            km
                        </span>

                        <span>
                            ⏱️
                            ${hospital.estimated_eta_minutes}
                            min ETA
                        </span>

                        <span>
                            🏥
                            ${hospital.current_occupancy}%
                            occupied
                        </span>

                    </div>

                </div>


                <div class="score-container">

                    <strong>
                        ${suitability}%
                    </strong>

                    <span>
                        Match
                    </span>

                </div>

            </div>


            <div class="hospital-status">

                ${
                    eligible
                        ? `
                            <span class="availability good">
                                ✓ All required resources available
                            </span>
                        `
                        : `
                            <span class="availability warning">
                                ⚠ ${escapeHTML(
                                    unavailable.join(", ")
                                )}
                            </span>
                        `
                }

            </div>


            ${
                reasons.length
                    ? `
                        <div class="reason-tags">

                            ${reasons
                                .map(
                                    reason =>
                                        `
                                        <span>
                                            ${escapeHTML(
                                                reason
                                            )}
                                        </span>
                                        `
                                )
                                .join("")}

                        </div>
                    `
                    : ""
            }


            ${
                eligible
                    ? `
                        <button
                            class="reserve-button"
                            onclick='reserveHospital(${JSON.stringify(
                                hospital
                            )})'
                        >
                            Reserve Emergency Resources
                            →
                        </button>
                    `
                    : ""
            }


        </div>

    `;
}


// ============================================================
// RESERVE
// ============================================================

async function reserveHospital(
    hospital
) {

    const patientName =
        document.getElementById(
            "name"
        ).value.trim();


    const resources =
        getSelectedResources();


    const workflow =
        document.getElementById(
            "workflow"
        );


    workflow.innerHTML = `

        <div class="loading-state small">

            <div class="large-spinner"></div>

            <h4>
                Creating reservation...
            </h4>

        </div>

    `;


    try {

        const data =
            await api(
                "/reserve",
                {
                    method: "POST",

                    body:
                        JSON.stringify({

                            hospital_id:
                                hospital.hospital_id,

                            hospital_name:
                                hospital.hospital_name,

                            patient_name:
                                patientName ||
                                "Emergency Patient",

                            required_resources:
                                resources

                        })
                }
            );


        selected =
            data.reservation;


        renderReservation(
            data.reservation
        );


        loadSummary();


    } catch (error) {

        workflow.innerHTML = `

            <div class="workflow-error">

                ⚠️ ${escapeHTML(
                    error.message
                )}

            </div>

        `;
    }
}


// ============================================================
// RESERVATION UI
// ============================================================

function renderReservation(
    reservation
) {

    const workflow =
        document.getElementById(
            "workflow"
        );


    workflow.innerHTML = `

        <div class="reservation-success">

            <div class="success-icon">
                ✓
            </div>

            <div>

                <span class="card-kicker">
                    RESERVATION CREATED
                </span>

                <h4>
                    ${escapeHTML(
                        reservation.hospital_name ||
                        "Hospital"
                    )}
                </h4>

                <p>
                    Reservation ID:
                    <strong>
                        ${escapeHTML(
                            reservation.reservation_id
                        )}
                    </strong>
                </p>

            </div>

        </div>


        <div class="reservation-status">

            <span>
                Current Status
            </span>

            <strong>
                ${escapeHTML(
                    reservation.status
                )}
            </strong>

        </div>


        <div class="workflow-actions">

            <button
                class="workflow-primary"
                onclick="confirmRes(
                    '${reservation.reservation_id}'
                )"
            >
                ✓ Hospital Confirms
            </button>

            <button
                class="workflow-secondary"
                onclick="cancelReservation(
                    '${reservation.reservation_id}'
                )"
            >
                Cancel Reservation
            </button>

        </div>

    `;
}


// ============================================================
// CONFIRM RESERVATION
// ============================================================

async function confirmRes(
    id
) {

    try {

        const data =
            await api(
                `/reservations/${id}/confirm`,
                {
                    method: "POST"
                }
            );


        document.getElementById(
            "workflow"
        ).innerHTML = `

            <div class="timeline">

                <div class="timeline-item completed">

                    <div class="timeline-number">
                        ✓
                    </div>

                    <div>

                        <strong>
                            Resources Reserved
                        </strong>

                        <p>
                            Hospital has confirmed
                            emergency resources.
                        </p>

                    </div>

                </div>


                <div class="timeline-item active">

                    <div class="timeline-number">
                        02
                    </div>

                    <div>

                        <strong>
                            Patient Transport
                        </strong>

                        <p>
                            Start ambulance transport
                            when ready.
                        </p>

                    </div>

                </div>

            </div>


            <div class="workflow-actions">

                <button
                    class="workflow-primary"
                    onclick="transport('${id}')"
                >
                    🚑 Start Transport
                </button>

            </div>

        `;


        loadSummary();


    } catch (error) {

        showWorkflowError(
            error.message
        );
    }
}


// ============================================================
// TRANSPORT
// ============================================================

async function transport(
    id
) {

    try {

        const data =
            await api(
                `/reservations/${id}/transport`,
                {
                    method: "POST"
                }
            );


        document.getElementById(
            "workflow"
        ).innerHTML = `

            <div class="timeline">

                <div class="timeline-item completed">

                    <div class="timeline-number">
                        ✓
                    </div>

                    <div>

                        <strong>
                            Resources Reserved
                        </strong>

                    </div>

                </div>


                <div class="timeline-item completed">

                    <div class="timeline-number">
                        ✓
                    </div>

                    <div>

                        <strong>
                            Patient In Transit
                        </strong>

                        <p>
                            Ambulance transport has started.
                        </p>

                    </div>

                </div>


                <div class="timeline-item active">

                    <div class="timeline-number">
                        03
                    </div>

                    <div>

                        <strong>
                            Hospital Arrival
                        </strong>

                        <p>
                            Mark the patient as arrived
                            after reaching the hospital.
                        </p>

                    </div>

                </div>

            </div>


            <div class="workflow-actions">

                <button
                    class="workflow-primary"
                    onclick="arrive('${id}')"
                >
                    🏥 Mark Arrived
                </button>

            </div>

        `;


    } catch (error) {

        showWorkflowError(
            error.message
        );
    }
}


// ============================================================
// ARRIVE
// ============================================================

async function arrive(
    id
) {

    try {

        await api(
            `/reservations/${id}/arrive`,
            {
                method: "POST"
            }
        );


        document.getElementById(
            "workflow"
        ).innerHTML = `

            <div class="timeline">

                <div class="timeline-item completed">

                    <div class="timeline-number">
                        ✓
                    </div>

                    <div>

                        <strong>
                            Resources Reserved
                        </strong>

                    </div>

                </div>


                <div class="timeline-item completed">

                    <div class="timeline-number">
                        ✓
                    </div>

                    <div>

                        <strong>
                            Patient In Transit
                        </strong>

                    </div>

                </div>


                <div class="timeline-item completed">

                    <div class="timeline-number">
                        ✓
                    </div>

                    <div>

                        <strong>
                            Patient Arrived
                        </strong>

                    </div>

                </div>


                <div class="timeline-item active">

                    <div class="timeline-number">
                        04
                    </div>

                    <div>

                        <strong>
                            Admission
                        </strong>

                        <p>
                            Complete admission at
                            the receiving hospital.
                        </p>

                    </div>

                </div>

            </div>


            <div class="workflow-actions">

                <button
                    class="workflow-primary"
                    onclick="admit('${id}')"
                >
                    ✓ Admit Patient
                </button>

            </div>

        `;


    } catch (error) {

        showWorkflowError(
            error.message
        );
    }
}


// ============================================================
// ADMIT
// ============================================================

async function admit(
    id
) {

    try {

        const data =
            await api(
                `/reservations/${id}/admit`,
                {
                    method: "POST"
                }
            );


        document.getElementById(
            "workflow"
        ).innerHTML = `

            <div class="completed-workflow">

                <div class="completed-icon">
                    ✓
                </div>

                <h3>
                    Patient Successfully Admitted
                </h3>

                <p>
                    The emergency care coordination
                    workflow has been completed.
                </p>

                <div class="completion-id">

                    Reservation ID:
                    <strong>
                        ${escapeHTML(
                            data.reservation.reservation_id
                        )}
                    </strong>

                </div>

            </div>

        `;


        loadSummary();


    } catch (error) {

        showWorkflowError(
            error.message
        );
    }
}


// ============================================================
// CANCEL RESERVATION
// ============================================================

async function cancelReservation(
    id
) {

    try {

        await api(
            `/reservations/${id}/cancel`,
            {
                method: "POST"
            }
        );


        document.getElementById(
            "workflow"
        ).innerHTML = `

            <div class="cancelled-workflow">

                <div>
                    ×
                </div>

                <h4>
                    Reservation Cancelled
                </h4>

                <p>
                    Hospital resources have been released.
                </p>

            </div>

        `;


        loadSummary();


    } catch (error) {

        showWorkflowError(
            error.message
        );
    }
}


// ============================================================
// ERROR DISPLAY
// ============================================================

function showResultsError(
    message
) {

    document.getElementById(
        "results"
    ).innerHTML = `

        <div class="error-state">

            <div>
                ⚠️
            </div>

            <h4>
                Unable to complete matching
            </h4>

            <p>
                ${escapeHTML(message)}
            </p>

        </div>

    `;
}


function showWorkflowError(
    message
) {

    document.getElementById(
        "workflow"
    ).innerHTML = `

        <div class="workflow-error">

            ⚠️ ${escapeHTML(message)}

        </div>

    `;
}


// ============================================================
// HTML SECURITY
// ============================================================

function escapeHTML(
    value
) {

    if (value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)
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


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        if (!currentUser) return;


        loadUserInformation();

        loadSummary();

    }
);