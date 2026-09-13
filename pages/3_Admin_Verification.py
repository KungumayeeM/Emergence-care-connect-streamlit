import streamlit as st

from Backend.database import (
    get_all_hospitals,
    get_hospital,
    update_registration_status
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Admin Verification",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ Admin Verification Portal")

st.write(
    "Review and verify hospital registrations before they "
    "become part of the EmergencyCare Connect verified network."
)

st.divider()


# ============================================================
# GET HOSPITAL DATA
# ============================================================

hospitals = get_all_hospitals()

pending_hospitals = [
    hospital
    for hospital in hospitals
    if hospital.get("registration_status") == "PENDING"
]

verified_hospitals = [
    hospital
    for hospital in hospitals
    if hospital.get("registration_status") == "VERIFIED"
]

rejected_hospitals = [
    hospital
    for hospital in hospitals
    if hospital.get("registration_status") == "REJECTED"
]


# ============================================================
# NETWORK STATUS
# ============================================================

st.header("📊 Registration Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Hospitals",
        len(hospitals)
    )

with col2:
    st.metric(
        "Pending",
        len(pending_hospitals)
    )

with col3:
    st.metric(
        "Verified",
        len(verified_hospitals)
    )

with col4:
    st.metric(
        "Rejected",
        len(rejected_hospitals)
    )

st.divider()


# ============================================================
# PENDING REGISTRATIONS
# ============================================================

st.header("🟠 Pending Hospital Registrations")

if not pending_hospitals:

    st.success(
        "✅ There are no pending hospital registrations."
    )

else:

    st.write(
        "The following hospitals are waiting for administrator verification."
    )

    pending_options = {}

    for hospital in pending_hospitals:

        hospital_id = hospital["hospital_id"]

        hospital_name = hospital["hospital_name"]

        pending_options[hospital_id] = (
            hospital_name
            + " ("
            + hospital_id
            + ")"
        )


    selected_id = st.selectbox(
        "Select a hospital to review",
        options=list(pending_options.keys()),
        format_func=lambda hospital_id:
            pending_options[hospital_id]
    )


    hospital = get_hospital(selected_id)


    if hospital:

        st.divider()

        # ----------------------------------------------------
        # HOSPITAL BASIC INFORMATION
        # ----------------------------------------------------

        st.subheader(
            "🏥 " + str(hospital["hospital_name"])
        )

        info_col1, info_col2, info_col3 = st.columns(3)

        with info_col1:

            st.write("**Hospital ID**")

            st.write(
                str(hospital["hospital_id"])
            )

        with info_col2:

            st.write("**Hospital Type**")

            st.write(
                str(hospital["hospital_type"])
            )

        with info_col3:

            st.write("**Registration Status**")

            st.warning(
                str(hospital["registration_status"])
            )


        st.divider()


        # ----------------------------------------------------
        # REGISTRATION DETAILS
        # ----------------------------------------------------

        st.subheader("📋 Registration Details")

        registration_col1, registration_col2 = st.columns(2)

        with registration_col1:

            st.write(
                "**Registration / License Number**"
            )

            st.write(
                str(
                    hospital["registration_number"]
                    or "Not provided"
                )
            )

        with registration_col2:

            st.write(
                "**Registered At**"
            )

            st.write(
                str(
                    hospital["registered_at"]
                    or "Not available"
                )
            )


        # ----------------------------------------------------
        # CONTACT DETAILS
        # ----------------------------------------------------

        st.subheader("📞 Contact Information")

        contact_col1, contact_col2 = st.columns(2)

        with contact_col1:

            st.write("**Contact Number**")

            st.write(
                str(
                    hospital["contact_number"]
                    or "Not provided"
                )
            )

        with contact_col2:

            st.write("**Official Email**")

            st.write(
                str(
                    hospital["official_email"]
                    or "Not provided"
                )
            )


        st.write("**Hospital Address**")

        st.write(
            str(
                hospital["address"]
                or "Not provided"
            )
        )


        # ----------------------------------------------------
        # ADMINISTRATOR
        # ----------------------------------------------------

        st.subheader("👤 Authorized Representative")

        st.write(
            str(
                hospital["administrator_name"]
                or "Not provided"
            )
        )


        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        st.subheader("📍 Hospital Location")

        location_col1, location_col2 = st.columns(2)

        with location_col1:

            st.metric(
                "Latitude",
                str(hospital["latitude"])
            )

        with location_col2:

            st.metric(
                "Longitude",
                str(hospital["longitude"])
            )


        # ----------------------------------------------------
        # EMERGENCY CAPACITY
        # ----------------------------------------------------

        st.subheader("🛏️ Emergency Capacity")

        capacity_col1, capacity_col2, capacity_col3, capacity_col4 = st.columns(4)

        with capacity_col1:

            st.metric(
                "Emergency Beds",
                hospital["emergency_beds"]
            )

        with capacity_col2:

            st.metric(
                "Total ICU Beds",
                hospital["icu_total"]
            )

        with capacity_col3:

            st.metric(
                "Available ICU",
                hospital["icu_available"]
            )

        with capacity_col4:

            st.metric(
                "Ventilators",
                hospital["ventilator_available"]
            )


        # ----------------------------------------------------
        # MEDICAL RESOURCES
        # ----------------------------------------------------

        st.subheader("🩺 Medical Resources")

        resource_col1, resource_col2, resource_col3 = st.columns(3)

        with resource_col1:

            if hospital["oxygen_available"] == "Yes":

                st.success(
                    "🟢 Oxygen Available"
                )

            else:

                st.error(
                    "🔴 Oxygen Unavailable"
                )


        with resource_col2:

            if hospital["blood_available"] == "Yes":

                st.success(
                    "🟢 Blood Available"
                )

            else:

                st.error(
                    "🔴 Blood Unavailable"
                )


        with resource_col3:

            if hospital["trauma_care"] == "Yes":

                st.success(
                    "🟢 Trauma Care Available"
                )

            else:

                st.error(
                    "🔴 Trauma Care Unavailable"
                )


        # ----------------------------------------------------
        # SPECIALISTS
        # ----------------------------------------------------

        st.subheader("👨‍⚕️ Specialist Services")

        specialist_col1, specialist_col2, specialist_col3, specialist_col4 = st.columns(4)

        with specialist_col1:

            if hospital["cardiologist"] == "Yes":

                st.success(
                    "🟢 Cardiologist"
                )

            else:

                st.error(
                    "🔴 Cardiologist"
                )


        with specialist_col2:

            if hospital["neurologist"] == "Yes":

                st.success(
                    "🟢 Neurologist"
                )

            else:

                st.error(
                    "🔴 Neurologist"
                )


        with specialist_col3:

            if hospital["orthopedic"] == "Yes":

                st.success(
                    "🟢 Orthopedic"
                )

            else:

                st.error(
                    "🔴 Orthopedic"
                )


        with specialist_col4:

            if hospital["surgery"] == "Yes":

                st.success(
                    "🟢 Emergency Surgery"
                )

            else:

                st.error(
                    "🔴 Emergency Surgery"
                )


        # ----------------------------------------------------
        # OCCUPANCY
        # ----------------------------------------------------

        st.subheader("📈 Current Occupancy")

        occupancy = float(
            hospital["current_occupancy"]
            or 0
        )

        st.progress(
            int(occupancy)
            / 100
        )

        st.write(
            "**Current Occupancy:** "
            + str(occupancy)
            + "%"
        )


        # ====================================================
        # ADMINISTRATOR DECISION
        # ====================================================

        st.divider()

        st.subheader("⚖️ Verification Decision")

        st.write(
            "Review the submitted information carefully "
            "before approving this hospital."
        )


        decision_col1, decision_col2 = st.columns(2)


        with decision_col1:

            if st.button(
                "✅ Approve Hospital",
                type="primary",
                use_container_width=True
            ):

                try:

                    updated_hospital = update_registration_status(
                        selected_id,
                        "VERIFIED"
                    )

                    if updated_hospital:

                        st.success(
                            "✅ Hospital "
                            + str(selected_id)
                            + " has been verified successfully."
                        )

                        st.info(
                            "The hospital is now marked as VERIFIED."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Unable to verify the hospital."
                        )

                except Exception as error:

                    st.error(
                        "An error occurred while verifying the hospital."
                    )

                    st.exception(error)


        with decision_col2:

            if st.button(
                "❌ Reject Hospital",
                use_container_width=True
            ):

                try:

                    updated_hospital = update_registration_status(
                        selected_id,
                        "REJECTED"
                    )

                    if updated_hospital:

                        st.warning(
                            "Hospital "
                            + str(selected_id)
                            + " has been rejected."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Unable to reject the hospital."
                        )

                except Exception as error:

                    st.error(
                        "An error occurred while rejecting the hospital."
                    )

                    st.exception(error)


# ============================================================
# VERIFIED HOSPITALS
# ============================================================

st.divider()

st.header("🟢 Verified Hospitals")

if verified_hospitals:

    for hospital in verified_hospitals:

        with st.expander(
            "🏥 "
            + str(hospital["hospital_name"])
            + " — "
            + str(hospital["hospital_id"])
        ):

            verified_col1, verified_col2, verified_col3 = st.columns(3)

            with verified_col1:

                st.write("**Hospital Type**")

                st.write(
                    str(hospital["hospital_type"])
                )

            with verified_col2:

                st.write("**Emergency Beds**")

                st.write(
                    str(hospital["emergency_beds"])
                )

            with verified_col3:

                st.write("**ICU Available**")

                st.write(
                    str(hospital["icu_available"])
                )

            st.success(
                "🟢 VERIFIED — Hospital is part of the verified network."
            )

else:

    st.info(
        "No verified hospitals found."
    )


# ============================================================
# REJECTED HOSPITALS
# ============================================================

st.divider()

st.header("🔴 Rejected Registrations")

if rejected_hospitals:

    for hospital in rejected_hospitals:

        with st.expander(
            "🏥 "
            + str(hospital["hospital_name"])
            + " — "
            + str(hospital["hospital_id"])
        ):

            st.write(
                "**Registration Number:** "
                + str(
                    hospital["registration_number"]
                    or "Not provided"
                )
            )

            st.write(
                "**Administrator:** "
                + str(
                    hospital["administrator_name"]
                    or "Not provided"
                )
            )

            st.error(
                "🔴 REJECTED"
            )

else:

    st.info(
        "No rejected registrations."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EmergencyCare Connect | Administrator Verification Portal"
)