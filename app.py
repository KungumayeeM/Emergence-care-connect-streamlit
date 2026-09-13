import streamlit as st
import pandas as pd
from pathlib import Path

from streamlit_geolocation import streamlit_geolocation
from ai.hospital_matching import match_hospitals
from Backend.reservation import reserve_hospital_resources
from Backend.auth import (
    is_logged_in,
    show_login_page,
    get_current_user,
    get_current_role,
    logout_button,
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "matching_results" not in st.session_state:
    st.session_state.matching_results = None

if "patient_data" not in st.session_state:
    st.session_state.patient_data = None

if "ambulance_location" not in st.session_state:
    st.session_state.ambulance_location = None

if "reservation_result" not in st.session_state:
    st.session_state.reservation_result = None


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="EmergencyCare Connect",
    page_icon="🚑",
    layout="wide"
)


# ---------------------------------------------------------
# LOAD PROFESSIONAL CSS
# ---------------------------------------------------------

def load_css():

    css_path = Path(__file__).resolve().parent / "static" / "style.css"

    if css_path.exists():

        with open(css_path, "r", encoding="utf-8") as file:

            css_code = file.read()

        st.markdown(
            "<style>" + css_code + "</style>",
            unsafe_allow_html=True
        )


# ---------------------------------------------------------
# LOAD JAVASCRIPT
# ---------------------------------------------------------

def load_javascript():

    js_path = Path(__file__).resolve().parent / "static" / "script.js"

    if js_path.exists():

        with open(js_path, "r", encoding="utf-8") as file:

            js_code = file.read()

        st.components.v1.html(
            "<script>" + js_code + "</script>",
            height=0
        )


load_css()
load_javascript()


# ---------------------------------------------------------
# LOGIN GATE
# ---------------------------------------------------------

if not is_logged_in():

    show_login_page()
    st.stop()


# ---------------------------------------------------------
# PATIENT ATTENDANT ACCESS
# ---------------------------------------------------------

current_role = get_current_role()

if current_role != "Patient Attendant":

    st.error(
        "This module is available only to Patient Attendant accounts."
    )

    st.info(
        "Use the appropriate module for your registered role."
    )

    logout_button()
    st.stop()


# ---------------------------------------------------------
# CURRENT USER
# ---------------------------------------------------------

current_user = get_current_user()

# auth.py may return either a dictionary or a username string.
# Normalize it here so the UI never calls .get() on a string.
if isinstance(current_user, dict):

    display_name = current_user.get(
        "full_name",
        current_user.get("username", "Patient Attendant")
    )

    display_role = current_user.get(
        "role",
        current_role
    )

else:

    display_name = str(current_user) if current_user else "Patient Attendant"
    display_role = current_role


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ec-hero">

        <div class="ec-hero-title">
            🚑 EmergencyCare Connect
        </div>

        <div class="ec-hero-text">
            AI-Assisted Emergency Hospital Coordination
        </div>

        <div style="margin-top:15px;font-size:14px;opacity:0.92;">
            Find the right hospital based on emergency requirements,
            available resources, location, estimated travel time
            and capacity freshness.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# EMERGENCY NOTICE
# ---------------------------------------------------------

st.markdown(
    """
    <div class="emergency-alert">
        <div class="emergency-alert-title">
            🚨 Emergency Coordination
        </div>
        <div class="emergency-alert-text">
            Enter the patient's emergency details and use the
            location service to identify suitable hospitals.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 5px 20px 5px;
        ">
            <div style="font-size:42px;">🚑</div>
            <div style="
                font-size:21px;
                font-weight:800;
            ">
                EmergencyCare
            </div>
            <div style="
                font-size:21px;
                font-weight:800;
            ">
                Connect
            </div>
            <div style="
                font-size:12px;
                opacity:0.85;
                margin-top:5px;
            ">
                Emergency Coordination Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        """
        <div style="
            padding:12px;
            border-radius:12px;
            background:rgba(255,255,255,0.10);
            margin-bottom:15px;
        ">
        """,
        unsafe_allow_html=True
    )

    st.write("👤 **" + str(display_name) + "**")
    st.caption("Role: " + str(display_role))

    st.markdown("</div>", unsafe_allow_html=True)

    st.info(
        "The system recommends hospitals using emergency "
        "requirements, resource availability, distance, ETA "
        "and capacity information."
    )

    st.divider()

    st.markdown(
        """
        <div style="
            padding:12px;
            border-radius:10px;
            background:rgba(255,255,255,0.08);
            font-size:13px;
        ">
        <b>Patient Attendant Module</b><br><br>
        Emergency request → GPS → AI hospital matching →
        resource reservation.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    logout_button()

    st.divider()

    st.caption(
        "EmergencyCare Connect is a prototype and does not "
        "replace professional medical judgment or emergency services."
    )


# ---------------------------------------------------------
# PATIENT INFORMATION
# ---------------------------------------------------------

st.header("👤 Patient Information")

col1, col2, col3 = st.columns(3)

with col1:

    patient_name = st.text_input(
        "Patient Name",
        placeholder="Enter patient name"
    )

with col2:

    age = st.number_input(
        "Age",
        min_value=0,
        max_value=120,
        value=25
    )

with col3:

    emergency_type = st.selectbox(
        "Emergency Type",
        [
            "Accident",
            "Cardiac Emergency",
            "Breathing Emergency",
            "Stroke",
            "Trauma",
            "Burn",
            "Other Emergency"
        ]
    )


# ---------------------------------------------------------
# EMERGENCY CONDITION
# ---------------------------------------------------------

st.header("🚨 Emergency Condition")

condition_col1, condition_col2, condition_col3 = st.columns(3)

with condition_col1:

    severity = st.selectbox(
        "Severity",
        [
            "Critical",
            "Severe",
            "Moderate",
            "Stable"
        ]
    )

with condition_col2:

    consciousness = st.selectbox(
        "Consciousness",
        [
            "Conscious",
            "Unconscious"
        ]
    )

with condition_col3:

    breathing = st.selectbox(
        "Breathing",
        [
            "Normal",
            "Difficult",
            "Not Breathing"
        ]
    )


bleeding = st.selectbox(
    "Bleeding",
    [
        "No",
        "Minor",
        "Severe"
    ]
)


# ---------------------------------------------------------
# REQUIRED RESOURCES
# ---------------------------------------------------------

st.header("🏥 Required Emergency Resources")

st.write(
    "Select the resources required by the patient."
)

required_resources = st.multiselect(
    "Required Resources",
    [
        "emergency_bed",
        "icu",
        "ventilator",
        "oxygen",
        "blood",
        "trauma",
        "surgery"
    ],
    default=["emergency_bed"]
)


# ---------------------------------------------------------
# SPECIALIST
# ---------------------------------------------------------

specialist = st.selectbox(
    "Required Specialist",
    [
        "None",
        "cardiologist",
        "neurologist",
        "orthopedic"
    ]
)


st.divider()


# ---------------------------------------------------------
# CURRENT LOCATION
# ---------------------------------------------------------

st.header("📍 Ambulance / Patient Location")

st.write(
    "Use your device's current location to calculate the "
    "real distance and estimated travel time to hospitals."
)

location = streamlit_geolocation()


# Default values before GPS is available
latitude = None
longitude = None
accuracy = None


# ---------------------------------------------------------
# CHECK GPS LOCATION
# ---------------------------------------------------------

if isinstance(location, dict):

    if (
        location.get("latitude") is not None
        and location.get("longitude") is not None
    ):

        latitude = location.get("latitude")
        longitude = location.get("longitude")
        accuracy = location.get("accuracy")

        st.success("📍 Current location detected successfully.")

        location_col1, location_col2, location_col3 = st.columns(3)

        with location_col1:

            st.metric(
                "Latitude",
                round(latitude, 6)
            )

        with location_col2:

            st.metric(
                "Longitude",
                round(longitude, 6)
            )

        with location_col3:

            if accuracy is not None:

                st.metric(
                    "GPS Accuracy",
                    str(round(accuracy, 1)) + " m"
                )

            else:

                st.metric(
                    "GPS Accuracy",
                    "Available"
                )

    else:

        st.info(
            "📍 Click the location button above and allow "
            "browser location permission."
        )

else:

    st.info(
        "📍 Click the location button above and allow "
        "browser location permission."
    )


st.divider()


# ---------------------------------------------------------
# FIND SUITABLE HOSPITAL
# ---------------------------------------------------------

find_button = st.button(
    "🚑 Find Suitable Hospitals",
    type="primary",
    use_container_width=True
)


if find_button:

    # -----------------------------------------------------
    # CHECK WHETHER GPS IS AVAILABLE
    # -----------------------------------------------------

    if latitude is None or longitude is None:

        st.warning(
            "📍 Please get your current location before "
            "finding a suitable hospital."
        )

    # -----------------------------------------------------
    # CHECK REQUIRED RESOURCES
    # -----------------------------------------------------

    elif len(required_resources) == 0:

        st.warning(
            "Please select at least one required emergency resource."
        )

    else:

        # -------------------------------------------------
        # PATIENT DATA
        # -------------------------------------------------

        patient = {
            "name": patient_name,
            "age": age,
            "emergency_type": emergency_type,
            "consciousness": consciousness,
            "breathing": breathing,
            "bleeding": bleeding,
            "severity": severity,
            "required_resources": required_resources,
            "specialist": (
                ""
                if specialist == "None"
                else specialist
            )
        }


        # -------------------------------------------------
        # CURRENT GPS LOCATION
        # -------------------------------------------------

        ambulance_location = {
            "latitude": latitude,
            "longitude": longitude
        }


        # -------------------------------------------------
        # RUN AI HOSPITAL MATCHING
        # -------------------------------------------------

        with st.spinner(
            "🤖 Analyzing hospitals and finding the best match..."
        ):

            results = match_hospitals(
                patient,
                ambulance_location
            )

        # Save the results because Streamlit reruns the script
        # whenever the Reserve Hospital button is clicked.
        st.session_state.matching_results = results
        st.session_state.patient_data = patient
        st.session_state.ambulance_location = ambulance_location
        st.session_state.reservation_result = None


# ---------------------------------------------------------
# DISPLAY MATCHING RESULTS
# ---------------------------------------------------------

results = st.session_state.matching_results


if results is not None:

    # -----------------------------------------------------
    # CHECK RESULTS
    # -----------------------------------------------------

    if not results:

        st.error(
            "No hospitals were found."
        )

    else:

        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        st.success(
            "Hospital matching completed successfully."
        )


        # -------------------------------------------------
        # BEST HOSPITAL
        # -------------------------------------------------

        best_hospital = results[0]

        st.header("🏆 Recommended Hospital")

        st.subheader(
            best_hospital["hospital_name"]
        )


        # -------------------------------------------------
        # BEST HOSPITAL METRICS
        # -------------------------------------------------

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:

            st.metric(
                "Suitability Score",
                str(best_hospital["suitability_score"]) + "/100"
            )

        with metric_col2:

            st.metric(
                "Distance",
                str(best_hospital["distance_km"]) + " km"
            )

        with metric_col3:

            st.metric(
                "Estimated ETA",
                str(best_hospital["estimated_eta_minutes"]) + " min"
            )

        with metric_col4:

            st.metric(
                "Current Occupancy",
                str(best_hospital["current_occupancy"]) + "%"
            )


        # -------------------------------------------------
        # ELIGIBILITY
        # -------------------------------------------------

        if best_hospital["eligible"]:

            st.success(
                "✅ All requested resources are currently available."
            )

        else:

            st.warning(
                "⚠️ This hospital does not fully satisfy all "
                "requested resources."
            )


        # -------------------------------------------------
        # RESERVE RECOMMENDED HOSPITAL
        # -------------------------------------------------

        if best_hospital["eligible"]:

            st.subheader("🚑 Reserve Hospital")

            if st.button(
                "🔒 Reserve Hospital",
                type="primary",
                use_container_width=True
            ):

                patient = st.session_state.patient_data
                ambulance_location = st.session_state.ambulance_location

                with st.spinner(
                    "Reserving emergency resources..."
                ):

                    reservation_result = reserve_hospital_resources(
                        hospital_id=best_hospital["hospital_id"],
                        patient_name=patient["name"],
                        patient_age=patient["age"],
                        emergency_type=patient["emergency_type"],
                        severity=patient["severity"],
                        required_resources=patient["required_resources"],
                        ambulance_latitude=ambulance_location["latitude"],
                        ambulance_longitude=ambulance_location["longitude"]
                    )

                st.session_state.reservation_result = reservation_result


            # -------------------------------------------------
            # RESERVATION RESULT
            # -------------------------------------------------

            if st.session_state.reservation_result is not None:

                reservation_result = st.session_state.reservation_result

                if reservation_result["success"]:

                    st.success(
                        "✅ Hospital resources reserved successfully."
                    )

                    st.info(
                        "Reservation ID: "
                        + str(
                            reservation_result["reservation_id"]
                        )
                    )

                    st.write(
                        "**Hospital:** "
                        + best_hospital["hospital_name"]
                    )

                    st.write(
                        "**Reserved Resources:** "
                        + ", ".join(
                            reservation_result["reserved_resources"]
                        )
                    )

                else:

                    st.error(
                        "❌ "
                        + str(reservation_result["message"])
                    )


        # -------------------------------------------------
        # DISTRICT INFORMATION
        # -------------------------------------------------

        st.info(
            "📍 District: "
            + str(best_hospital.get("district", "Unknown"))
            + " | "
            + str(best_hospital.get("district_match", "Unknown"))
        )


        # -------------------------------------------------
        # MATCHING REASONS
        # -------------------------------------------------

        st.subheader("🔎 Why this hospital was recommended")

        for reason in best_hospital["reasons"]:

            st.write(
                "• " + reason
            )


        # -------------------------------------------------
        # UNAVAILABLE REQUIREMENTS
        # -------------------------------------------------

        if best_hospital["unavailable_requirements"]:

            st.warning(
                "Unavailable requirements: "
                + ", ".join(
                    best_hospital["unavailable_requirements"]
                )
            )


        st.divider()


        # -------------------------------------------------
        # RANKED HOSPITALS
        # -------------------------------------------------

        st.header("📊 Hospital Ranking")

        ranking_data = []

        for hospital in results:

            ranking_data.append({
                "Rank": len(ranking_data) + 1,

                "Hospital":
                    hospital["hospital_name"],

                "District":
                    hospital.get(
                        "district",
                        "Unknown"
                    ),

                "District Match":
                    hospital.get(
                        "district_match",
                        "Unknown"
                    ),

                "Type":
                    hospital["hospital_type"],

                "Score":
                    hospital["suitability_score"],

                "Distance (km)":
                    hospital["distance_km"],

                "ETA (min)":
                    hospital["estimated_eta_minutes"],

                "Occupancy (%)":
                    hospital["current_occupancy"],

                "Suitable":
                    (
                        "Yes"
                        if hospital["eligible"]
                        else "No"
                    )
            })


        ranking_df = pd.DataFrame(
            ranking_data
        )


        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        # -------------------------------------------------
        # HOSPITAL DETAILS
        # -------------------------------------------------

        st.header("🏥 Hospital Details")


        for hospital in results:

            with st.expander(
                hospital["hospital_name"]
                + " — Score "
                + str(hospital["suitability_score"])
            ):

                detail_col1, detail_col2 = st.columns(2)


                with detail_col1:

                    st.write(
                        "**Hospital Type:** "
                        + str(hospital["hospital_type"])
                    )

                    st.write(
                        "**District:** "
                        + str(
                            hospital.get(
                                "district",
                                "Unknown"
                            )
                        )
                    )

                    st.write(
                        "**District Match:** "
                        + str(
                            hospital.get(
                                "district_match",
                                "Unknown"
                            )
                        )
                    )

                    st.write(
                        "**Distance:** "
                        + str(hospital["distance_km"])
                        + " km"
                    )

                    st.write(
                        "**Estimated ETA:** "
                        + str(hospital["estimated_eta_minutes"])
                        + " minutes"
                    )

                    st.write(
                        "**Current Occupancy:** "
                        + str(hospital["current_occupancy"])
                        + "%"
                    )


                with detail_col2:

                    st.write(
                        "**Capacity Freshness:** "
                        + str(
                            hospital[
                                "capacity_freshness_minutes"
                            ]
                        )
                        + " minutes"
                    )

                    st.write(
                        "**Suitable:** "
                        + (
                            "Yes"
                            if hospital["eligible"]
                            else "No"
                        )
                    )


                st.write("**Matching Reasons:**")

                for reason in hospital["reasons"]:

                    st.write(
                        "• " + reason
                    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "EmergencyCare Connect | AI-Assisted Emergency Hospital Coordination Prototype"
)