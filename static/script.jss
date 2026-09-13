/* ============================================================
   EmergencyCare Connect
   Frontend JavaScript
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    console.log("EmergencyCare Connect frontend loaded.");

    initializeAnimations();
    initializeStatusBadges();
    initializeAutoRefreshIndicator();
});


/* ------------------------------------------------------------
   Smooth card animations
   ------------------------------------------------------------ */

function initializeAnimations() {

    const cards = document.querySelectorAll(
        ".ec-card, .hospital-card, .metric-card, .ambulance-card, .reservation-card"
    );

    cards.forEach(function (card) {

        card.addEventListener("mouseenter", function () {
            card.style.transition = "transform 0.2s ease, box-shadow 0.2s ease";
        });

    });
}


/* ------------------------------------------------------------
   Status badge styling
   ------------------------------------------------------------ */

function initializeStatusBadges() {

    const badges = document.querySelectorAll(".status-badge");

    badges.forEach(function (badge) {

        const status = badge.textContent.trim().toUpperCase();

        if (
            status.includes("AVAILABLE") ||
            status.includes("ACTIVE") ||
            status.includes("CONFIRMED")
        ) {
            badge.classList.add("status-available");
        }

        else if (
            status.includes("ON_CALL") ||
            status.includes("IN_TRANSIT") ||
            status.includes("EN_ROUTE") ||
            status.includes("ARRIVED")
        ) {
            badge.classList.add("status-active");
        }

        else if (
            status.includes("WARNING") ||
            status.includes("PENDING")
        ) {
            badge.classList.add("status-warning");
        }

        else if (
            status.includes("CANCELLED") ||
            status.includes("EXPIRED") ||
            status.includes("CRITICAL")
        ) {
            badge.classList.add("status-danger");
        }

        else {
            badge.classList.add("status-neutral");
        }

    });
}


/* ------------------------------------------------------------
   Emergency alert animation
   ------------------------------------------------------------ */

function highlightEmergencyAlerts() {

    const alerts = document.querySelectorAll(".emergency-alert");

    alerts.forEach(function (alert) {

        alert.style.transition = "box-shadow 0.5s ease";

        alert.addEventListener("mouseenter", function () {
            alert.style.boxShadow =
                "0 6px 20px rgba(220, 53, 69, 0.20)";
        });

        alert.addEventListener("mouseleave", function () {
            alert.style.boxShadow = "none";
        });

    });
}


/* ------------------------------------------------------------
   Current time
   ------------------------------------------------------------ */

function getCurrentTime() {

    const now = new Date();

    return now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}


/* ------------------------------------------------------------
   Auto refresh indicator
   ------------------------------------------------------------ */

function initializeAutoRefreshIndicator() {

    const elements = document.querySelectorAll(".live-time");

    if (elements.length === 0) {
        return;
    }

    function updateClock() {

        const currentTime = getCurrentTime();

        elements.forEach(function (element) {
            element.textContent = currentTime;
        });

    }

    updateClock();

    setInterval(updateClock, 1000);
}


/* ------------------------------------------------------------
   Update element text
   ------------------------------------------------------------ */

function updateElement(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }

}


/* ------------------------------------------------------------
   Show temporary notification
   ------------------------------------------------------------ */

function showNotification(message, type) {

    const notification = document.createElement("div");

    notification.textContent = message;

    notification.style.position = "fixed";
    notification.style.top = "20px";
    notification.style.right = "20px";
    notification.style.zIndex = "9999";
    notification.style.padding = "14px 20px";
    notification.style.borderRadius = "10px";
    notification.style.fontWeight = "600";
    notification.style.background = "#ffffff";
    notification.style.boxShadow =
        "0 8px 25px rgba(15, 23, 42, 0.18)";

    if (type === "success") {
        notification.style.borderLeft = "5px solid #198754";
    }

    else if (type === "error") {
        notification.style.borderLeft = "5px solid #dc3545";
    }

    else {
        notification.style.borderLeft = "5px solid #0b5ed7";
    }

    document.body.appendChild(notification);

    setTimeout(function () {
        notification.remove();
    }, 3000);

}


/* ------------------------------------------------------------
   Confirm emergency action
   ------------------------------------------------------------ */

function confirmEmergencyAction(message) {

    return window.confirm(
        message || "Are you sure you want to continue?"
    );

}


/* ------------------------------------------------------------
   Browser location helper
   ------------------------------------------------------------ */

function requestBrowserLocation() {

    if (!navigator.geolocation) {

        console.log("Geolocation is not supported.");

        return;

    }

    navigator.geolocation.getCurrentPosition(

        function (position) {

            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;

            console.log("Latitude:", latitude);
            console.log("Longitude:", longitude);

            const latitudeElement =
                document.getElementById("browser-latitude");

            const longitudeElement =
                document.getElementById("browser-longitude");

            if (latitudeElement) {
                latitudeElement.textContent = latitude;
            }

            if (longitudeElement) {
                longitudeElement.textContent = longitude;
            }

        },

        function (error) {

            console.log(
                "Location permission/error:",
                error.message
            );

        }

    );

}


/* ------------------------------------------------------------
   Page visibility monitoring
   ------------------------------------------------------------ */

document.addEventListener(
    "visibilitychange",
    function () {

        if (document.hidden) {
            console.log("EmergencyCare Connect tab is inactive.");
        }

        else {
            console.log("EmergencyCare Connect tab is active.");
        }

    }
);