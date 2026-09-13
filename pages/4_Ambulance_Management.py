import streamlit as st
from datetime import datetime

from Backend.database import (
    get_all_ambulances,
    register_ambulance,
    update_ambulance_status,
    update_ambulance_location
)


st.set_page_config(
    page_title="Ambulance Management",
    page_icon="🚑",
    layout="wide"
)


st.title("🚑 Ambulance Management")

st.write(
    "Register and monitor ambulances used by "
    "EmergencyCare Connect."
)

st.divider()


# =========================================================
# REGISTER AMBULANCE
# =========================================================

st.header("➕ Register Ambulance")

col1, col2 = st.columns(2)

with col1:

    ambulance_id = st.text_input(
        "Ambulance ID",
        placeholder="AMB001"
    )

    vehicle_number = st.text_input(
        "Vehicle Number",
        placeholder="TN01AB1234"
    )

    driver_name = st.text_input(
        "Driver Name"
    )


with col2:

    nurse_name = st.text_input(
        "Nurse Name"
    )

    coordinator_name = st.text_input(
        "Coordinator Name"
    )

    ambulance_latitude = st.number_input(
        "Current Latitude",
        value=0.0,
        format="%.6f"
    )

    ambulance_longitude = st.number_input(
        "Current Longitude",
        value=0.0,
        format="%.6f"
    )


if st.button(
    "🚑 Register Ambulance",
    type="primary",
    use_container_width=True
):

    if not ambulance_id:

        st.warning(
            "Please enter an ambulance ID."
        )

    elif not vehicle_number:

        st.warning(
            "Please enter the vehicle number."
        )

    else:

        latitude = ambulance_latitude

        longitude = ambulance_longitude

        if latitude == 0.0 and longitude == 0.0:

            latitude = None
            longitude = None

        success = register_ambulance(
            ambulance_id,
            vehicle_number,
            driver_name,
            nurse_name,
            coordinator_name,
            latitude,
            longitude
        )

        if success:

            st.success(
                "✅ Ambulance registered successfully."
            )

            st.rerun()

        else:

            st.error(
                "❌ Ambulance ID already exists."
            )


st.divider()


# =========================================================
# REGISTERED AMBULANCES
# =========================================================

st.header("📋 Registered Ambulances")

ambulances = get_all_ambulances()


if not ambulances:

    st.info(
        "No ambulances are currently registered."
    )

else:

    for ambulance in ambulances:

        ambulance_id = ambulance.get(
            "ambulance_id",
            ""
        )

        status = ambulance.get(
            "status",
            "UNKNOWN"
        )

        if status == "AVAILABLE":

            status_label = "🟢 AVAILABLE"

        elif status == "ON_CALL":

            status_label = "🟡 ON CALL"

        elif status == "IN_TRANSIT":

            status_label = "🔵 IN TRANSIT"

        elif status == "ARRIVED":

            status_label = "🏥 ARRIVED"

        else:

            status_label = "🔴 " + str(status)

        with st.expander(
            "🚑 "
            + str(ambulance_id)
            + " — "
            + status_label
        ):

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    "**Vehicle:** "
                    + str(
                        ambulance.get(
                            "vehicle_number",
                            ""
                        )
                    )
                )

                st.write(
                    "**Driver:** "
                    + str(
                        ambulance.get(
                            "driver_name",
                            ""
                        )
                    )
                )

            with col2:

                st.write(
                    "**Nurse:** "
                    + str(
                        ambulance.get(
                            "nurse_name",
                            ""
                        )
                    )
                )

                st.write(
                    "**Coordinator:** "
                    + str(
                        ambulance.get(
                            "coordinator_name",
                            ""
                        )
                    )
                )

            with col3:

                st.write(
                    "**Latitude:** "
                    + str(
                        ambulance.get(
                            "latitude",
                            ""
                        )
                    )
                )

                st.write(
                    "**Longitude:** "
                    + str(
                        ambulance.get(
                            "longitude",
                            ""
                        )
                    )
                )

            st.write(
                "**Last Updated:** "
                + str(
                    ambulance.get(
                        "last_updated",
                        ""
                    )
                )
            )

            st.divider()

            new_status = st.selectbox(
                "Update Status",
                [
                    "AVAILABLE",
                    "ON_CALL",
                    "IN_TRANSIT",
                    "ARRIVED",
                    "UNAVAILABLE"
                ],
                index=[
                    "AVAILABLE",
                    "ON_CALL",
                    "IN_TRANSIT",
                    "ARRIVED",
                    "UNAVAILABLE"
                ].index(status)
                if status in [
                    "AVAILABLE",
                    "ON_CALL",
                    "IN_TRANSIT",
                    "ARRIVED",
                    "UNAVAILABLE"
                ]
                else 0,
                key="status_" + str(ambulance_id)
            )

            if st.button(
                "💾 Update Status",
                key="update_status_" + str(ambulance_id),
                use_container_width=True
            ):

                success = update_ambulance_status(
                    ambulance_id,
                    new_status
                )

                if success:

                    st.success(
                        "Ambulance status updated."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Unable to update ambulance status."
                    )


st.divider()

st.caption(
    "EmergencyCare Connect | Database-backed Ambulance Management"
)