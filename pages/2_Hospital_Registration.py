import streamlit as st
from datetime import datetime

from Backend.database import register_hospital


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Hospital Registration",
    page_icon="🏥",
    layout="wide"
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🏥 Hospital Registration Portal")

st.write(
    "Register your hospital with EmergencyCare Connect "
    "to participate in the emergency hospital network."
)

st.info(
    "New hospital registrations are submitted for verification. "
    "The hospital will receive PENDING status until approved."
)

st.divider()


# ============================================================
# HOSPITAL INFORMATION
# ============================================================

st.header("🏥 Hospital Information")

col1, col2 = st.columns(2)

with col1:

    hospital_name = st.text_input(
        "Hospital Name *",
        placeholder="Enter official hospital name"
    )

with col2:

    hospital_type = st.selectbox(
        "Hospital Type *",
        [
            "Government",
            "Private",
            "Specialty",
            "Trust",
            "Other"
        ]
    )


registration_number = st.text_input(
    "Hospital Registration / License Number *",
    placeholder="Enter registration or license number"
)


# ============================================================
# CONTACT INFORMATION
# ============================================================

st.header("📞 Contact Information")

contact_col1, contact_col2 = st.columns(2)

with contact_col1:

    contact_number = st.text_input(
        "Hospital Contact Number *",
        placeholder="Enter official contact number"
    )

with contact_col2:

    official_email = st.text_input(
        "Official Hospital Email *",
        placeholder="hospital@example.com"
    )


address = st.text_area(
    "Hospital Address *",
    placeholder="Enter complete hospital address",
    height=100
)


# ============================================================
# LOCATION
# ============================================================

st.header("📍 Hospital Location")

location_col1, location_col2 = st.columns(2)

with location_col1:

    latitude = st.number_input(
        "Latitude *",
        value=13.0827,
        format="%.6f"
    )

with location_col2:

    longitude = st.number_input(
        "Longitude *",
        value=80.2707,
        format="%.6f"
    )

st.caption(
    "Enter the geographical coordinates of the hospital. "
    "These coordinates are used for hospital matching and distance calculation."
)


# ============================================================
# EMERGENCY CAPACITY
# ============================================================

st.header("🛏️ Emergency Capacity")

capacity_col1, capacity_col2, capacity_col3 = st.columns(3)

with capacity_col1:

    emergency_beds = st.number_input(
        "Emergency Beds Available *",
        min_value=0,
        value=0,
        step=1
    )

with capacity_col2:

    icu_total = st.number_input(
        "Total ICU Beds *",
        min_value=0,
        value=0,
        step=1
    )

with capacity_col3:

    icu_available = st.number_input(
        "Currently Available ICU Beds *",
        min_value=0,
        value=0,
        step=1
    )


ventilator_available = st.number_input(
    "Ventilators Available *",
    min_value=0,
    value=0,
    step=1
)


# ============================================================
# MEDICAL RESOURCES
# ============================================================

st.header("🩺 Medical Resources")

resource_col1, resource_col2, resource_col3 = st.columns(3)

with resource_col1:

    oxygen_available = st.selectbox(
        "Oxygen Availability",
        ["Yes", "No"]
    )

with resource_col2:

    blood_available = st.selectbox(
        "Blood Availability",
        ["Yes", "No"]
    )

with resource_col3:

    trauma_care = st.selectbox(
        "Trauma Care",
        ["Yes", "No"]
    )


# ============================================================
# SPECIALIST SERVICES
# ============================================================

st.header("👨‍⚕️ Specialist Availability")

specialist_col1, specialist_col2 = st.columns(2)

with specialist_col1:

    cardiologist = st.selectbox(
        "Cardiologist",
        ["Yes", "No"]
    )

with specialist_col2:

    neurologist = st.selectbox(
        "Neurologist",
        ["Yes", "No"]
    )


specialist_col3, specialist_col4 = st.columns(2)

with specialist_col3:

    orthopedic = st.selectbox(
        "Orthopedic Specialist",
        ["Yes", "No"]
    )

with specialist_col4:

    surgery = st.selectbox(
        "Emergency Surgery",
        ["Yes", "No"]
    )


# ============================================================
# ADMINISTRATOR INFORMATION
# ============================================================

st.header("👤 Hospital Administrator")

administrator_name = st.text_input(
    "Administrator / Authorized Representative *",
    placeholder="Enter administrator name"
)


# ============================================================
# REGISTRATION DECLARATION
# ============================================================

st.header("📋 Registration Declaration")

declaration = st.checkbox(
    "I confirm that the information provided above is accurate "
    "and represents the current emergency facilities available "
    "at this hospital."
)


# ============================================================
# SUBMIT REGISTRATION
# ============================================================

st.divider()

if st.button(
    "🏥 Submit Hospital Registration",
    type="primary",
    use_container_width=True
):

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not hospital_name.strip():

        st.error(
            "Please enter the hospital name."
        )

    elif not registration_number.strip():

        st.error(
            "Please enter the hospital registration or license number."
        )

    elif not contact_number.strip():

        st.error(
            "Please enter the hospital contact number."
        )

    elif not official_email.strip():

        st.error(
            "Please enter the official hospital email."
        )

    elif not address.strip():

        st.error(
            "Please enter the hospital address."
        )

    elif not administrator_name.strip():

        st.error(
            "Please enter the administrator name."
        )

    elif icu_available > icu_total:

        st.error(
            "Available ICU beds cannot be greater than total ICU beds."
        )

    elif not declaration:

        st.error(
            "Please confirm the registration declaration."
        )

    else:

        # ----------------------------------------------------
        # PREPARE REGISTRATION DATA
        # ----------------------------------------------------

        hospital_data = {

            "hospital_name":
                hospital_name.strip(),

            "hospital_type":
                hospital_type,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "emergency_beds":
                emergency_beds,

            "icu_total":
                icu_total,

            "icu_available":
                icu_available,

            "ventilator_available":
                ventilator_available,

            "oxygen_available":
                oxygen_available,

            "blood_available":
                blood_available,

            "trauma_care":
                trauma_care,

            "cardiologist":
                cardiologist,

            "neurologist":
                neurologist,

            "orthopedic":
                orthopedic,

            "surgery":
                surgery,

            "current_occupancy":
                0,

            "last_updated":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "registration_number":
                registration_number.strip(),

            "contact_number":
                contact_number.strip(),

            "official_email":
                official_email.strip(),

            "address":
                address.strip(),

            "administrator_name":
                administrator_name.strip(),

            "registered_at":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }


        # ----------------------------------------------------
        # SAVE REGISTRATION
        # ----------------------------------------------------

        try:

            hospital_id = register_hospital(
                hospital_data
            )

            st.success(
                "✅ Hospital registration submitted successfully."
            )

            st.divider()

            st.subheader(
                "📋 Registration Submitted"
            )

            result_col1, result_col2 = st.columns(2)

            with result_col1:

                st.metric(
                    "Hospital ID",
                    hospital_id
                )

            with result_col2:

                st.metric(
                    "Registration Status",
                    "PENDING"
                )


            st.info(
                "Your registration has been submitted for verification. "
                "The hospital will become part of the verified emergency "
                "network after approval."
            )

            st.warning(
                "⚠️ Keep your Hospital ID for future reference: "
                + hospital_id
            )


        except Exception as error:

            st.error(
                "Unable to submit hospital registration."
            )

            st.exception(error)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EmergencyCare Connect | Hospital Registration Portal"
)