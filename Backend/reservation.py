from datetime import datetime, timedelta
import sqlite3

from Backend.database import (
    DATABASE,
    get_hospital,
    get_connection,
    assign_available_ambulance,
    update_ambulance_status,
    release_ambulance,
)


# ============================================================
# RESERVATION TABLE
# ============================================================

def initialize_reservation_table():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id TEXT PRIMARY KEY,
            hospital_id TEXT,
            hospital_name TEXT,
            patient_name TEXT,
            patient_age INTEGER,
            emergency_type TEXT,
            severity TEXT,
            required_resources TEXT,
            ambulance_latitude REAL,
            ambulance_longitude REAL,
            ambulance_id TEXT,
            status TEXT DEFAULT 'CONFIRMED',
            reserved_at TEXT,
            created_at TEXT,
            expires_at TEXT,
            confirmed_at TEXT,
            transport_started_at TEXT,
            arrived_at TEXT,
            admitted_at TEXT,
            discharged_at TEXT,
            cancelled_at TEXT,
            notes TEXT
        )
        """
    )

    connection.commit()

    # --------------------------------------------------------
    # Safe migration for older reservation databases
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(reservations)")
    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    required_columns = {
        "hospital_name": "TEXT",
        "patient_age": "INTEGER",
        "emergency_type": "TEXT",
        "severity": "TEXT",
        "required_resources": "TEXT",
        "ambulance_latitude": "REAL",
        "ambulance_longitude": "REAL",
        "ambulance_id": "TEXT",
        "status": "TEXT DEFAULT 'CONFIRMED'",
        "reserved_at": "TEXT",
        "created_at": "TEXT",
        "expires_at": "TEXT",
        "confirmed_at": "TEXT",
        "transport_started_at": "TEXT",
        "arrived_at": "TEXT",
        "admitted_at": "TEXT",
        "discharged_at": "TEXT",
        "cancelled_at": "TEXT",
        "notes": "TEXT",
    }

    for column_name, column_type in required_columns.items():

        if column_name not in existing_columns:

            try:
                cursor.execute(
                    "ALTER TABLE reservations ADD COLUMN "
                    + column_name
                    + " "
                    + column_type
                )
            except sqlite3.OperationalError:
                pass

    connection.commit()
    connection.close()


initialize_reservation_table()


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def generate_reservation_id():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM reservations"
    )

    count = cursor.fetchone()[0]

    connection.close()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    return "RES-" + timestamp + "-" + str(count + 1)


def get_hospital_by_id(hospital_id):

    hospital = get_hospital(hospital_id)

    if hospital is None:
        return None

    return hospital


def parse_required_resources(required_resources):

    if required_resources is None:
        return []

    if isinstance(required_resources, list):
        return required_resources

    if isinstance(required_resources, tuple):
        return list(required_resources)

    if isinstance(required_resources, str):

        if required_resources.strip() == "":
            return []

        return [
            item.strip()
            for item in required_resources.split(",")
            if item.strip()
        ]

    return []


# ============================================================
# RESOURCE MANAGEMENT
# ============================================================

def check_resource_availability(hospital_id, required_resources):

    hospital = get_hospital_by_id(hospital_id)

    if hospital is None:
        return False

    resources = parse_required_resources(required_resources)

    for resource in resources:

        resource_name = resource.lower().strip()

        if resource_name in [
            "emergency bed",
            "emergency_bed",
            "emergency beds",
        ]:

            if int(hospital.get("emergency_beds", 0)) <= 0:
                return False

        elif resource_name in ["icu", "icu bed", "icu beds"]:

            if int(hospital.get("icu_available", 0)) <= 0:
                return False

        elif resource_name in [
            "ventilator",
            "ventilators",
        ]:

            if int(hospital.get("ventilator_available", 0)) <= 0:
                return False

        elif resource_name in [
            "oxygen",
            "oxygen support",
        ]:

            if int(hospital.get("oxygen_available", 0)) <= 0:
                return False

        elif resource_name in [
            "blood",
            "blood bank",
        ]:

            if int(hospital.get("blood_available", 0)) <= 0:
                return False

    return True


def reduce_hospital_capacity(hospital_id, required_resources):

    resources = parse_required_resources(required_resources)

    connection = get_connection()

    cursor = connection.cursor()

    try:

        for resource in resources:

            resource_name = resource.lower().strip()

            column_name = None

            if resource_name in [
                "emergency bed",
                "emergency_bed",
                "emergency beds",
            ]:
                column_name = "emergency_beds"

            elif resource_name in [
                "icu",
                "icu bed",
                "icu beds",
            ]:
                column_name = "icu_available"

            elif resource_name in [
                "ventilator",
                "ventilators",
            ]:
                column_name = "ventilator_available"

            elif resource_name in [
                "oxygen",
                "oxygen support",
            ]:
                column_name = "oxygen_available"

            elif resource_name in [
                "blood",
                "blood bank",
            ]:
                column_name = "blood_available"

            if column_name is None:
                continue

            cursor.execute(
                "SELECT "
                + column_name
                + " FROM hospitals WHERE hospital_id = ?",
                (hospital_id,)
            )

            row = cursor.fetchone()

            if row is None or int(row[0] or 0) <= 0:

                connection.rollback()
                connection.close()

                return False

            cursor.execute(
                "UPDATE hospitals SET "
                + column_name
                + " = "
                + column_name
                + " - 1, "
                + "last_updated = ? "
                + "WHERE hospital_id = ?",
                (
                    datetime.now().isoformat(),
                    hospital_id,
                )
            )

        connection.commit()
        connection.close()

        return True

    except Exception:

        connection.rollback()
        connection.close()

        return False


def restore_resource(hospital_id, required_resources):

    resources = parse_required_resources(required_resources)

    connection = get_connection()

    cursor = connection.cursor()

    try:

        for resource in resources:

            resource_name = resource.lower().strip()

            column_name = None

            if resource_name in [
                "emergency bed",
                "emergency_bed",
                "emergency beds",
            ]:
                column_name = "emergency_beds"

            elif resource_name in [
                "icu",
                "icu bed",
                "icu beds",
            ]:
                column_name = "icu_available"

            elif resource_name in [
                "ventilator",
                "ventilators",
            ]:
                column_name = "ventilator_available"

            elif resource_name in [
                "oxygen",
                "oxygen support",
            ]:
                column_name = "oxygen_available"

            elif resource_name in [
                "blood",
                "blood bank",
            ]:
                column_name = "blood_available"

            if column_name is None:
                continue

            cursor.execute(
                "UPDATE hospitals SET "
                + column_name
                + " = "
                + column_name
                + " + 1, "
                + "last_updated = ? "
                + "WHERE hospital_id = ?",
                (
                    datetime.now().isoformat(),
                    hospital_id,
                )
            )

        connection.commit()
        connection.close()

        return True

    except Exception:

        connection.rollback()
        connection.close()

        return False


# ============================================================
# CREATE RESERVATION
# ============================================================

def create_reservation(
    hospital_id,
    patient_name,
    patient_age=None,
    emergency_type=None,
    severity=None,
    required_resources=None,
    ambulance_latitude=None,
    ambulance_longitude=None,
    expires_minutes=30,
):

    hospital = get_hospital_by_id(hospital_id)

    if hospital is None:
        return {
            "success": False,
            "message": "Hospital not found."
        }

    reservation_id = generate_reservation_id()

    now = datetime.now()

    expires_at = now + timedelta(
        minutes=expires_minutes
    )

    resources = parse_required_resources(
        required_resources
    )

    required_resources_text = ", ".join(resources)

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reservations (
            reservation_id,
            hospital_id,
            hospital_name,
            patient_name,
            patient_age,
            emergency_type,
            severity,
            required_resources,
            ambulance_latitude,
            ambulance_longitude,
            ambulance_id,
            status,
            reserved_at,
            created_at,
            expires_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reservation_id,
            hospital_id,
            hospital.get("hospital_name", ""),
            patient_name,
            patient_age,
            emergency_type,
            severity,
            required_resources_text,
            ambulance_latitude,
            ambulance_longitude,
            None,
            "CONFIRMED",
            now.isoformat(),
            now.isoformat(),
            expires_at.isoformat(),
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "hospital_id": hospital_id,
        "hospital_name": hospital.get(
            "hospital_name",
            ""
        ),
        "reserved_resources": resources,
        "status": "CONFIRMED",
        "expires_at": expires_at.isoformat(),
    }


# ============================================================
# RESERVE HOSPITAL RESOURCES
# ============================================================

def reserve_hospital_resources(
    hospital_id,
    patient_name,
    required_resources=None,
    patient_age=None,
    emergency_type=None,
    severity=None,
    ambulance_latitude=None,
    ambulance_longitude=None,
):

    resources = parse_required_resources(
        required_resources
    )

    if not check_resource_availability(
        hospital_id,
        resources
    ):
        return {
            "success": False,
            "message": "Required hospital resources are not available."
        }

    reduced = reduce_hospital_capacity(
        hospital_id,
        resources
    )

    if not reduced:
        return {
            "success": False,
            "message": "Unable to reserve hospital resources."
        }

    result = create_reservation(
        hospital_id=hospital_id,
        patient_name=patient_name,
        patient_age=patient_age,
        emergency_type=emergency_type,
        severity=severity,
        required_resources=resources,
        ambulance_latitude=ambulance_latitude,
        ambulance_longitude=ambulance_longitude,
    )

    if not result.get("success"):

        restore_resource(
            hospital_id,
            resources
        )

        return result

    return result


# ============================================================
# GET RESERVATION
# ============================================================

def get_reservation(reservation_id):

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservations
        WHERE reservation_id = ?
        """,
        (reservation_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def get_hospital_reservations(hospital_id):

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservations
        WHERE hospital_id = ?
        ORDER BY created_at DESC
        """,
        (hospital_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# AMBULANCE ASSIGNMENT
# ============================================================

def assign_ambulance_to_reservation(
    reservation_id,
    latitude=None,
    longitude=None,
):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    existing_ambulance = reservation.get(
        "ambulance_id"
    )

    if existing_ambulance:

        return {
            "success": True,
            "ambulance_id": existing_ambulance,
            "status": "ON_CALL",
            "message": "Ambulance already assigned."
        }

    ambulance = assign_available_ambulance(
        latitude=latitude,
        longitude=longitude
    )

    if ambulance is None:

        return {
            "success": False,
            "message": "No available ambulance."
        }

    ambulance_id = ambulance.get(
        "ambulance_id"
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET ambulance_id = ?
        WHERE reservation_id = ?
        """,
        (
            ambulance_id,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "ambulance_id": ambulance_id,
        "vehicle_number": ambulance.get(
            "vehicle_number"
        ),
        "driver_name": ambulance.get(
            "driver_name"
        ),
        "nurse_name": ambulance.get(
            "nurse_name"
        ),
        "coordinator_name": ambulance.get(
            "coordinator_name"
        ),
        "status": "ON_CALL",
        "message": "Ambulance assigned successfully."
    }


def get_reservation_ambulance(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:
        return None

    ambulance_id = reservation.get(
        "ambulance_id"
    )

    if not ambulance_id:
        return None

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM ambulances
        WHERE ambulance_id = ?
        """,
        (ambulance_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


# ============================================================
# START PATIENT TRANSPORT
# ============================================================

def start_patient_transport(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    ambulance_id = reservation.get(
        "ambulance_id"
    )

    if not ambulance_id:

        return {
            "success": False,
            "message": "No ambulance is assigned to this reservation."
        }

    current_status = reservation.get(
        "status"
    )

    if current_status not in [
        "CONFIRMED",
        "ON_CALL",
    ]:

        return {
            "success": False,
            "message": (
                "Transport cannot be started from status "
                + str(current_status)
            )
        }

    update_ambulance_status(
        ambulance_id,
        "EN_ROUTE"
    )

    now = datetime.now().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?,
            transport_started_at = ?
        WHERE reservation_id = ?
        """,
        (
            "IN_TRANSIT",
            now,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "ambulance_id": ambulance_id,
        "status": "IN_TRANSIT",
        "message": "Ambulance is now en route to the hospital."
    }


# ============================================================
# AMBULANCE ARRIVAL
# ============================================================

def mark_patient_arrived(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    ambulance_id = reservation.get(
        "ambulance_id"
    )

    current_status = reservation.get(
        "status"
    )

    if current_status not in [
        "IN_TRANSIT",
        "EN_ROUTE",
    ]:

        return {
            "success": False,
            "message": (
                "Patient cannot be marked arrived from status "
                + str(current_status)
            )
        }

    now = datetime.now().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?,
            arrived_at = ?
        WHERE reservation_id = ?
        """,
        (
            "ARRIVED",
            now,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    # Ambulance becomes available for the next emergency.
    if ambulance_id:

        release_ambulance(
            ambulance_id
        )

    return {
        "success": True,
        "reservation_id": reservation_id,
        "ambulance_id": ambulance_id,
        "status": "ARRIVED",
        "message": "Patient has arrived at the hospital."
    }


# ============================================================
# ADMIT PATIENT
# ============================================================

def admit_reserved_patient(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    current_status = reservation.get(
        "status"
    )

    if current_status != "ARRIVED":

        return {
            "success": False,
            "message": (
                "Patient must arrive before admission. "
                "Current status: "
                + str(current_status)
            )
        }

    now = datetime.now().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?,
            admitted_at = ?
        WHERE reservation_id = ?
        """,
        (
            "ADMITTED",
            now,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "status": "ADMITTED",
        "message": "Patient admitted successfully."
    }


# ============================================================
# DISCHARGE PATIENT
# ============================================================

def discharge_admitted_patient(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    current_status = reservation.get(
        "status"
    )

    if current_status != "ADMITTED":

        return {
            "success": False,
            "message": (
                "Patient must be admitted before discharge."
            )
        }

    hospital_id = reservation.get(
        "hospital_id"
    )

    resources = parse_required_resources(
        reservation.get(
            "required_resources"
        )
    )

    restore_resource(
        hospital_id,
        resources
    )

    now = datetime.now().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?,
            discharged_at = ?
        WHERE reservation_id = ?
        """,
        (
            "DISCHARGED",
            now,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "status": "DISCHARGED",
        "message": "Patient discharged and resources restored."
    }


# ============================================================
# CANCEL RESERVATION
# ============================================================

def cancel_reservation(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    current_status = reservation.get(
        "status"
    )

    if current_status in [
        "CANCELLED",
        "EXPIRED",
        "DISCHARGED",
    ]:

        return {
            "success": False,
            "message": "Reservation is already closed."
        }

    hospital_id = reservation.get(
        "hospital_id"
    )

    resources = parse_required_resources(
        reservation.get(
            "required_resources"
        )
    )

    restore_resource(
        hospital_id,
        resources
    )

    ambulance_id = reservation.get(
        "ambulance_id"
    )

    if ambulance_id:

        release_ambulance(
            ambulance_id
        )

    now = datetime.now().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?,
            cancelled_at = ?
        WHERE reservation_id = ?
        """,
        (
            "CANCELLED",
            now,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "status": "CANCELLED",
        "message": "Reservation cancelled and resources restored."
    }


# ============================================================
# EXPIRE RESERVATION
# ============================================================

def expire_reservation(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    current_status = reservation.get(
        "status"
    )

    if current_status in [
        "CANCELLED",
        "EXPIRED",
        "DISCHARGED",
        "ADMITTED",
    ]:

        return {
            "success": False,
            "message": "Reservation cannot be expired."
        }

    hospital_id = reservation.get(
        "hospital_id"
    )

    resources = parse_required_resources(
        reservation.get(
            "required_resources"
        )
    )

    restore_resource(
        hospital_id,
        resources
    )

    ambulance_id = reservation.get(
        "ambulance_id"
    )

    if ambulance_id:

        release_ambulance(
            ambulance_id
        )

    now = datetime.now().isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?
        WHERE reservation_id = ?
        """,
        (
            "EXPIRED",
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "status": "EXPIRED",
        "message": "Reservation expired and resources restored."
    }


# ============================================================
# EXPIRE OLD RESERVATIONS
# ============================================================

def expire_reservations():

    now = datetime.now()

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservations
        WHERE status IN ('CONFIRMED', 'ON_CALL')
        AND expires_at IS NOT NULL
        """
    )

    rows = cursor.fetchall()

    connection.close()

    expired_count = 0

    for row in rows:

        reservation = dict(row)

        expires_at_text = reservation.get(
            "expires_at"
        )

        if not expires_at_text:
            continue

        try:

            expires_at = datetime.fromisoformat(
                expires_at_text
            )

        except ValueError:

            continue

        if expires_at <= now:

            result = expire_reservation(
                reservation.get(
                    "reservation_id"
                )
            )

            if result.get("success"):
                expired_count += 1

    return expired_count


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def confirm_reservation(reservation_id):

    reservation = get_reservation(
        reservation_id
    )

    if reservation is None:

        return {
            "success": False,
            "message": "Reservation not found."
        }

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE reservations
        SET status = ?,
            confirmed_at = ?
        WHERE reservation_id = ?
        """,
        (
            "CONFIRMED",
            now,
            reservation_id,
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "status": "CONFIRMED",
        "message": "Reservation confirmed."
    }


def get_reservations():

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservations
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# BACKWARD-COMPATIBILITY ADMISSION FUNCTION
# ============================================================

def admit_patient(reservation_id):

    return admit_reserved_patient(
        reservation_id
    )