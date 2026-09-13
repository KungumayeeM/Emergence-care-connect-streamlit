import streamlit as st
from datetime import datetime

from Backend.database import (
    get_all_hospitals,
    get_hospital,
    update_hospital_capacity,
    capacity_summary
)

from Backend.reservation import (
    get_hospital_reservations,
    start_patient_transport,
    mark_patient_arrived,
    admit_reserved_patient,
    discharge_admitted_patient,
    cancel_reservation,
    expire_reservation
)


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Hospital Dashboard",
    page_icon="🏥",
    layout="wide"
)


# ==========================================================
# HEADER
# ==========================================================

st.title("🏥 Hospital Dashboard")

st.write(
    "Manage hospital emergency capacity, medical resources, "
    "specialists and availability used by EmergencyCare Connect."
)

st.divider()


# ==========================================================
# HOSPITAL NETWORK OVERVIEW
# ==========================================================

st.header("📊 Hospital Network Overview")

summary = capacity_summary()

# ----------------------------------------------------------
# Convert the current database summary into the values
# required by this dashboard.
# ----------------------------------------------------------

all_hospitals_for_summary = get_all_hospitals()

summary["hospital_count"] = summary.get(
    "hospital_count",
    summary.get("total_hospitals", 0)
)

summary["emergency_beds_available"] = sum(
    int(hospital_item.get("emergency_beds", 0))
    for hospital_item in all_hospitals_for_summary
)

summary["icu_available"] = sum(
    int(hospital_item.get("icu_available", 0))
    for hospital_item in all_hospitals_for_summary
)

summary["ventilators_available"] = sum(
    int(hospital_item.get("ventilator_available", 0))
    for hospital_item in all_hospitals_for_summary
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Registered Hospitals",
        summary["hospital_count"]
    )


with col2:

    st.metric(
        "Emergency Beds",
        summary["emergency_beds_available"]
    )


with col3:

    st.metric(
        "ICU Beds",
        summary["icu_available"]
    )


with col4:

    st.metric(
        "Ventilators",
        summary["ventilators_available"]
    )


st.divider()


# ==========================================================
# HOSPITAL SELECTION
# ==========================================================

st.header("🏥 Hospital Capacity Management")

hospitals = get_all_hospitals()


if not hospitals:

    st.error(
        "No hospitals are currently registered in the system."
    )

    st.stop()


hospital_options = {}


for hospital_item in hospitals:

    hospital_options[hospital_item["hospital_id"]] = (
        hospital_item["hospital_name"]
        + " ("
        + hospital_item["hospital_id"]
        + ")"
    )


selected_hospital_id = st.selectbox(
    "Select Hospital",
    options=list(hospital_options.keys()),
    format_func=lambda hospital_id:
        hospital_options[hospital_id]
)


hospital = get_hospital(
    selected_hospital_id
)


if hospital is None:

    st.error(
        "Selected hospital could not be found."
    )

    st.stop()


# ==========================================================
# HOSPITAL INFORMATION
# ==========================================================

st.subheader(
    "🏥 " + str(hospital["hospital_name"])
)


info_col1, info_col2, info_col3 = st.columns(3)


with info_col1:

    st.write(
        "**Hospital ID**"
    )

    st.write(
        str(hospital["hospital_id"])
    )


with info_col2:

    st.write(
        "**Hospital Type**"
    )

    st.write(
        str(hospital["hospital_type"])
    )


with info_col3:

    st.write(
        "**Hospital Location**"
    )

    st.write(
        str(hospital["latitude"])
        + ", "
        + str(hospital["longitude"])
    )


st.divider()


# ==========================================================
# CURRENT CAPACITY
# ==========================================================

st.subheader("🛏️ Current Capacity")


capacity_col1, capacity_col2, capacity_col3, capacity_col4 = st.columns(4)


with capacity_col1:

    st.metric(
        "Emergency Beds",
        hospital["emergency_beds"]
    )


with capacity_col2:

    st.metric(
        "ICU Available",
        hospital["icu_available"]
    )


with capacity_col3:

    st.metric(
        "Ventilators",
        hospital["ventilator_available"]
    )


with capacity_col4:

    st.metric(
        "Occupancy",
        str(hospital["current_occupancy"])
        + "%"
    )


st.divider()


# ==========================================================
# UPDATE HOSPITAL CAPACITY
# ==========================================================

st.subheader("✏️ Update Hospital Capacity")

st.write(
    "Update the current hospital availability. "
    "These values are used by the AI hospital matching engine."
)


update_col1, update_col2, update_col3 = st.columns(3)


with update_col1:

    emergency_beds = st.number_input(
        "Emergency Beds Available",
        min_value=0,
        value=int(
            hospital["emergency_beds"]
        ),
        step=1
    )


with update_col2:

    icu_available = st.number_input(
        "ICU Beds Available",
        min_value=0,
        max_value=int(
            hospital["icu_total"]
        ),
        value=int(
            hospital["icu_available"]
        ),
        step=1
    )


with update_col3:

    ventilator_available = st.number_input(
        "Ventilators Available",
        min_value=0,
        value=int(
            hospital["ventilator_available"]
        ),
        step=1
    )


# ==========================================================
# MEDICAL RESOURCES
# ==========================================================

st.subheader("🩺 Medical Resources")


resource_col1, resource_col2, resource_col3 = st.columns(3)


with resource_col1:

    oxygen_available = st.selectbox(
        "Oxygen Available",
        ["Yes", "No"],
        index=(
            0
            if hospital["oxygen_available"] == "Yes"
            else 1
        )
    )


with resource_col2:

    blood_available = st.selectbox(
        "Blood Available",
        ["Yes", "No"],
        index=(
            0
            if hospital["blood_available"] == "Yes"
            else 1
        )
    )


with resource_col3:

    trauma_care = st.selectbox(
        "Trauma Care",
        ["Yes", "No"],
        index=(
            0
            if hospital["trauma_care"] == "Yes"
            else 1
        )
    )


# ==========================================================
# SPECIALIST AVAILABILITY
# ==========================================================

st.subheader("👨‍⚕️ Specialist Availability")


specialist_col1, specialist_col2, specialist_col3 = st.columns(3)


with specialist_col1:

    cardiologist = st.selectbox(
        "Cardiologist",
        ["Yes", "No"],
        index=(
            0
            if hospital["cardiologist"] == "Yes"
            else 1
        )
    )


with specialist_col2:

    neurologist = st.selectbox(
        "Neurologist",
        ["Yes", "No"],
        index=(
            0
            if hospital["neurologist"] == "Yes"
            else 1
        )
    )


with specialist_col3:

    orthopedic = st.selectbox(
        "Orthopedic",
        ["Yes", "No"],
        index=(
            0
            if hospital["orthopedic"] == "Yes"
            else 1
        )
    )


surgery = st.selectbox(
    "Emergency Surgery Available",
    ["Yes", "No"],
    index=(
        0
        if hospital["surgery"] == "Yes"
        else 1
    )
)


# ==========================================================
# HOSPITAL OCCUPANCY
# ==========================================================

st.subheader("📈 Hospital Occupancy")


current_occupancy = st.slider(
    "Current Occupancy (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(
        hospital["current_occupancy"]
    ),
    step=1.0
)


# Occupancy progress bar

st.progress(
    int(current_occupancy) / 100
)


if current_occupancy >= 90:

    st.error(
        "🔴 Critical occupancy level"
    )

elif current_occupancy >= 75:

    st.warning(
        "🟠 High occupancy level"
    )

else:

    st.success(
        "🟢 Normal occupancy level"
    )


st.write(
    "**Previous Capacity Update:** "
    + str(hospital["last_updated"])
)


# ==========================================================
# SAVE HOSPITAL UPDATE
# ==========================================================

if st.button(
    "💾 Update Hospital Information",
    type="primary",
    use_container_width=True
):

    updates = {

        "emergency_beds":
            emergency_beds,

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
            current_occupancy,

        "last_updated":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    }


    updated_hospital = update_hospital_capacity(
        selected_hospital_id,
        updates
    )


    if updated_hospital:

        st.success(
            "✅ Hospital information updated successfully."
        )

        st.info(
            "The updated capacity is now available "
            "to the EmergencyCare Connect AI matching engine."
        )

        st.rerun()

    else:

        st.error(
            "Unable to update hospital information."
        )


st.divider()


# ==========================================================
# INTERACTIVE RESOURCE STATUS
# ==========================================================

st.header("🟢 Current Resource Status")

st.write(
    "Expand a category to view the current availability "
    "of hospital resources and services."
)


# ----------------------------------------------------------
# EMERGENCY RESOURCES
# ----------------------------------------------------------

with st.expander(
    "🚑 Emergency Resources",
    expanded=True
):

    emergency_col1, emergency_col2, emergency_col3 = st.columns(3)


    with emergency_col1:

        if hospital["emergency_beds"] > 0:

            st.success(
                "🟢 Emergency Beds\n\n"
                + str(
                    hospital["emergency_beds"]
                )
                + " beds available"
            )

        else:

            st.error(
                "🔴 Emergency Beds\n\n"
                "No beds available"
            )


    with emergency_col2:

        if hospital["icu_available"] > 0:

            st.success(
                "🟢 ICU Beds\n\n"
                + str(
                    hospital["icu_available"]
                )
                + " beds available"
            )

        else:

            st.error(
                "🔴 ICU Beds\n\n"
                "No ICU beds available"
            )


    with emergency_col3:

        if hospital["ventilator_available"] > 0:

            st.success(
                "🟢 Ventilators\n\n"
                + str(
                    hospital["ventilator_available"]
                )
                + " available"
            )

        else:

            st.error(
                "🔴 Ventilators\n\n"
                "None available"
            )


# ----------------------------------------------------------
# MEDICAL SERVICES
# ----------------------------------------------------------

with st.expander(
    "🩺 Medical Services"
):

    medical_col1, medical_col2, medical_col3 = st.columns(3)


    with medical_col1:

        if hospital["oxygen_available"] == "Yes":

            st.success(
                "🟢 Oxygen Available"
            )

        else:

            st.error(
                "🔴 Oxygen Unavailable"
            )


    with medical_col2:

        if hospital["blood_available"] == "Yes":

            st.success(
                "🟢 Blood Available"
            )

        else:

            st.error(
                "🔴 Blood Unavailable"
            )


    with medical_col3:

        if hospital["trauma_care"] == "Yes":

            st.success(
                "🟢 Trauma Care Available"
            )

        else:

            st.error(
                "🔴 Trauma Care Unavailable"
            )


# ----------------------------------------------------------
# SPECIALIST SERVICES
# ----------------------------------------------------------

with st.expander(
    "👨‍⚕️ Specialist Services"
):

    specialist_status_col1, specialist_status_col2, specialist_status_col3 = st.columns(3)


    with specialist_status_col1:

        if hospital["cardiologist"] == "Yes":

            st.success(
                "🟢 Cardiologist Available"
            )

        else:

            st.error(
                "🔴 Cardiologist Unavailable"
            )


    with specialist_status_col2:

        if hospital["neurologist"] == "Yes":

            st.success(
                "🟢 Neurologist Available"
            )

        else:

            st.error(
                "🔴 Neurologist Unavailable"
            )


    with specialist_status_col3:

        if hospital["orthopedic"] == "Yes":

            st.success(
                "🟢 Orthopedic Available"
            )

        else:

            st.error(
                "🔴 Orthopedic Unavailable"
            )


# ----------------------------------------------------------
# EMERGENCY SURGERY
# ----------------------------------------------------------

with st.expander(
    "🏥 Emergency Surgery"
):

    if hospital["surgery"] == "Yes":

        st.success(
            "🟢 Emergency Surgery Available"
        )

    else:

        st.error(
            "🔴 Emergency Surgery Unavailable"
        )


st.divider()


# ==========================================================
# LAST UPDATED INFORMATION
# ==========================================================

st.subheader("🕒 Capacity Information")


st.write(
    "**Hospital:** "
    + str(hospital["hospital_name"])
)


st.write(
    "**Last Updated:** "
    + str(hospital["last_updated"])
)


st.info(
    "Hospital availability data is used by EmergencyCare Connect "
    "to calculate suitable hospital recommendations."
)


st.divider()


# ==========================================================
# EMERGENCY RESERVATIONS
# ==========================================================

st.header("🚑 Emergency Reservations")
st.write("Manage incoming emergency patients and follow the complete ambulance-to-admission workflow.")

reservations = get_hospital_reservations(selected_hospital_id)

if not reservations:
    st.info("No emergency reservations are currently associated with this hospital.")
else:
    for reservation in reservations:
        reservation_id = reservation.get("reservation_id", "Unknown")
        patient_name = reservation.get("patient_name", "Unknown Patient")
        status = reservation.get("status", "UNKNOWN")
        severity = reservation.get("severity", "Not specified")
        emergency_type = reservation.get("emergency_type", "Not specified")
        ambulance_id = reservation.get("ambulance_id")

        with st.container(border=True):
            st.subheader("🧑‍⚕️ " + str(patient_name))
            c1,c2,c3=st.columns(3)
            with c1:
                st.write("**Reservation ID:** " + str(reservation_id))
                st.write("**Emergency:** " + str(emergency_type))
            with c2:
                st.write("**Severity:** " + str(severity))
                st.write("**Status:** " + str(status))
            with c3:
                st.write("**Ambulance:** " + (str(ambulance_id) if ambulance_id else "Not assigned"))

            if status == "CONFIRMED":
                st.info("Hospital reservation confirmed. Start ambulance transport when the patient is ready to travel.")
                if st.button("🚑 Start Transport", key="start_transport_"+str(reservation_id), use_container_width=True):
                    result=start_patient_transport(reservation_id)
                    if result.get("success"): st.success(result.get("message","Ambulance is now en route.")); st.rerun()
                    else: st.error(result.get("message","Unable to start transport."))
                if st.button("❌ Cancel Reservation", key="cancel_confirmed_"+str(reservation_id), use_container_width=True):
                    result=cancel_reservation(reservation_id)
                    if result.get("success"): st.success(result.get("message","Reservation cancelled.")); st.rerun()
                    else: st.error(result.get("message","Unable to cancel reservation."))

            elif status == "IN_TRANSIT":
                st.warning("🚑 Ambulance is currently en route.")
                if st.button("📍 Mark Patient Arrived", key="arrived_"+str(reservation_id), use_container_width=True):
                    result=mark_patient_arrived(reservation_id)
                    if result.get("success"): st.success(result.get("message","Patient marked as arrived.")); st.rerun()
                    else: st.error(result.get("message","Unable to mark patient arrived."))

            elif status == "ARRIVED":
                st.success("🟢 Patient has arrived at the hospital.")
                if st.button("🏥 Admit Patient", key="admit_"+str(reservation_id), use_container_width=True):
                    result=admit_reserved_patient(reservation_id)
                    if result.get("success"): st.success(result.get("message","Patient admitted successfully.")); st.rerun()
                    else: st.error(result.get("message","Unable to admit patient."))

            elif status == "ADMITTED":
                st.success("🛏️ Patient is currently admitted.")
                if st.button("✅ Discharge Patient", key="discharge_"+str(reservation_id), use_container_width=True):
                    result=discharge_admitted_patient(reservation_id)
                    if result.get("success"): st.success(result.get("message","Patient discharged successfully.")); st.rerun()
                    else: st.error(result.get("message","Unable to discharge patient."))
            elif status == "DISCHARGED": st.success("✅ Patient discharged and hospital resources have been restored.")
            elif status == "CANCELLED": st.info("Reservation cancelled. Reserved resources have been restored.")
            elif status == "EXPIRED": st.info("Reservation expired. Reserved resources have been restored.")
            else: st.warning("Unknown reservation status: " + str(status))

            if status in ["CONFIRMED", "IN_TRANSIT"]:
                if st.button("⏱️ Expire Reservation", key="expire_"+str(reservation_id), use_container_width=True):
                    result=expire_reservation(reservation_id)
                    if result.get("success"): st.success(result.get("message","Reservation expired.")); st.rerun()
                    else: st.error(result.get("message","Unable to expire reservation."))


st.divider()


# ==========================================================
# FOOTER
# ==========================================================

st.caption(
    "EmergencyCare Connect | Hospital Capacity Management"
)