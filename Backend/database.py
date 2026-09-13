import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "dataset" / "Hospitals.csv"

DATABASE = BASE_DIR / "Backend" / "emergencycare.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# LOAD HOSPITAL DATA FROM CSV
# ============================================================

def load_hospital_csv():

    hospitals = pd.read_csv(DATA_FILE)

    # Safety check for incorrectly parsed CSV rows
    if hospitals.iloc[:, 0].astype(str).str.contains(",").any():

        fixed = hospitals.iloc[:, 0].astype(str).str.split(
            ",",
            expand=True
        )

        fixed.columns = hospitals.columns

        hospitals = fixed

    return hospitals


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # HOSPITALS TABLE
    # --------------------------------------------------------

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS hospitals (

        hospital_id TEXT PRIMARY KEY,

        hospital_name TEXT NOT NULL,

        hospital_type TEXT,

        latitude REAL NOT NULL,

        longitude REAL NOT NULL,

        emergency_beds INTEGER DEFAULT 0,

        icu_total INTEGER DEFAULT 0,

        icu_available INTEGER DEFAULT 0,

        ventilator_available INTEGER DEFAULT 0,

        oxygen_available TEXT DEFAULT 'No',

        blood_available TEXT DEFAULT 'No',

        trauma_care TEXT DEFAULT 'No',

        cardiologist TEXT DEFAULT 'No',

        neurologist TEXT DEFAULT 'No',

        orthopedic TEXT DEFAULT 'No',

        surgery TEXT DEFAULT 'No',

        current_occupancy REAL DEFAULT 0,

        last_updated TEXT,

        registration_number TEXT,

        contact_number TEXT,

        official_email TEXT,

        address TEXT,

        administrator_name TEXT,

        registration_status TEXT DEFAULT 'VERIFIED',

        registered_at TEXT
    );


    -- -------------------------------------------------------
    -- PATIENTS TABLE
    -- -------------------------------------------------------

    CREATE TABLE IF NOT EXISTS patients (

        patient_id TEXT PRIMARY KEY,

        name TEXT,

        age INTEGER,

        gender TEXT,

        contact TEXT,

        blood_group TEXT,

        allergies TEXT,

        existing_conditions TEXT,

        medication TEXT,

        emergency_type TEXT,

        consciousness TEXT,

        breathing TEXT,

        bleeding TEXT,

        severity TEXT,

        required_resources TEXT,

        latitude REAL,

        longitude REAL,

        created_at TEXT
    );


    -- -------------------------------------------------------
    -- AMBULANCES TABLE
    -- -------------------------------------------------------

    CREATE TABLE IF NOT EXISTS ambulances (

        ambulance_id TEXT PRIMARY KEY,

        vehicle_number TEXT,

        driver_name TEXT,

        nurse_name TEXT,

        coordinator_name TEXT,

        latitude REAL,

        longitude REAL,

        status TEXT DEFAULT 'AVAILABLE',

        last_updated TEXT
    );


    -- -------------------------------------------------------
    -- RESERVATIONS TABLE
    -- -------------------------------------------------------

    CREATE TABLE IF NOT EXISTS reservations (

        reservation_id TEXT PRIMARY KEY,

        hospital_id TEXT NOT NULL,

        hospital_name TEXT NOT NULL,

        patient_id TEXT,

        patient_name TEXT,

        required_resources TEXT,

        status TEXT NOT NULL,

        created_at TEXT NOT NULL,

        expires_at TEXT NOT NULL,

        confirmed_at TEXT,

        transport_started_at TEXT,

        arrived_at TEXT,

        admitted_at TEXT,

        cancelled_at TEXT,

        notes TEXT
    );


    -- -------------------------------------------------------
    -- TRANSFERS TABLE
    -- -------------------------------------------------------

    CREATE TABLE IF NOT EXISTS transfers (

        transfer_id TEXT PRIMARY KEY,

        patient_id TEXT NOT NULL,

        source_hospital_id TEXT,

        destination_hospital_id TEXT,

        status TEXT,

        created_at TEXT,

        completed_at TEXT
    );
    """)


    # ========================================================
    # SAFE DATABASE MIGRATION
    # ========================================================

    existing_columns = {

        row["name"]

        for row in cursor.execute(
            "PRAGMA table_info(hospitals)"
        ).fetchall()
    }


    new_columns = {

        "registration_number":
            "TEXT",

        "contact_number":
            "TEXT",

        "official_email":
            "TEXT",

        "address":
            "TEXT",

        "administrator_name":
            "TEXT",

        "registration_status":
            "TEXT DEFAULT 'VERIFIED'",

        "registered_at":
            "TEXT"
    }


    for column_name, column_definition in new_columns.items():

        if column_name not in existing_columns:

            cursor.execute(
                "ALTER TABLE hospitals ADD COLUMN "
                + column_name
                + " "
                + column_definition
            )


    # ========================================================
    # INSERT ORIGINAL CSV HOSPITALS ONLY IF DATABASE IS EMPTY
    # ========================================================

    count = cursor.execute(
        "SELECT COUNT(*) FROM hospitals"
    ).fetchone()[0]


    if count == 0:

        hospitals = load_hospital_csv()

        cols = list(hospitals.columns)

        placeholders = ",".join(
            ["?"] * len(cols)
        )

        sql = (
            "INSERT INTO hospitals ("
            + ",".join(cols)
            + ") VALUES ("
            + placeholders
            + ")"
        )

        cursor.executemany(
            sql,
            [
                tuple(row)
                for _, row in hospitals.iterrows()
            ]
        )


    # ========================================================
    # EXISTING HOSPITALS ARE VERIFIED
    # ========================================================

    cursor.execute("""
        UPDATE hospitals

        SET registration_status = 'VERIFIED'

        WHERE registration_status IS NULL
    """)


    connection.commit()

    connection.close()


# ============================================================
# GET ALL HOSPITALS
# ============================================================

def get_all_hospitals(verified_only=False):

    connection = get_connection()


    if verified_only:

        rows = connection.execute(
            """
            SELECT *
            FROM hospitals
            WHERE registration_status = 'VERIFIED'
            ORDER BY hospital_name
            """
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT *
            FROM hospitals
            ORDER BY hospital_name
            """
        ).fetchall()


    connection.close()


    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET ONE HOSPITAL
# ============================================================

def get_hospital(hospital_id):

    connection = get_connection()


    row = connection.execute(
        """
        SELECT *
        FROM hospitals
        WHERE hospital_id = ?
        """,
        (hospital_id,)
    ).fetchone()


    connection.close()


    if row:

        return dict(row)


    return None


# ============================================================
# UPDATE HOSPITAL CAPACITY
# ============================================================

def update_hospital_capacity(
    hospital_id,
    updates
):
    """
    Safely update live hospital capacity/service information.

    This function is intentionally defensive because Streamlit widgets
    can sometimes return dictionaries or other non-scalar objects.
    SQLite parameters must be scalar values, so every value is converted
    before the SQL UPDATE is executed.
    """

    # --------------------------------------------------------
    # NORMALIZE HOSPITAL ID
    # --------------------------------------------------------

    def normalize_hospital_id(value):
        if isinstance(value, dict):
            if "hospital_id" in value:
                return normalize_hospital_id(value["hospital_id"])
            if "value" in value:
                return normalize_hospital_id(value["value"])
            if "label" in value:
                return normalize_hospital_id(value["label"])
            return None

        if hasattr(value, "keys") and not isinstance(
            value, (str, bytes, list, tuple, set)
        ):
            try:
                if "hospital_id" in value.keys():
                    return normalize_hospital_id(value["hospital_id"])
            except Exception:
                pass

        if value is None:
            return None

        return str(value)

    hospital_id = normalize_hospital_id(hospital_id)

    if not hospital_id:
        return None

    # --------------------------------------------------------
    # VALIDATE UPDATE DATA
    # --------------------------------------------------------

    if not isinstance(updates, dict):
        return get_hospital(hospital_id)

    allowed = {
        "emergency_beds",
        "icu_available",
        "ventilator_available",
        "oxygen_available",
        "blood_available",
        "trauma_care",
        "cardiologist",
        "neurologist",
        "orthopedic",
        "surgery",
        "current_occupancy",
        "last_updated"
    }

    # --------------------------------------------------------
    # CONVERT ANY VALUE TO AN SQLITE-SAFE VALUE
    # --------------------------------------------------------

    def sqlite_safe(value):
        """
        SQLite accepts None, int, float, str and bytes as bound values.
        Convert dictionaries/collections/other objects recursively.
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (str, int, float, bytes)):
            return value

        if isinstance(value, dict):
            # Prefer common widget/object keys.
            if "value" in value:
                return sqlite_safe(value["value"])

            if "label" in value:
                return sqlite_safe(value["label"])

            if "hospital_id" in value and len(value) == 1:
                return sqlite_safe(value["hospital_id"])

            # If a complete dictionary remains, store a readable string.
            parts = []
            for key, item in value.items():
                safe_item = sqlite_safe(item)

                if safe_item is not None:
                    parts.append(
                        str(key) + ": " + str(safe_item)
                    )

            return ", ".join(parts) if parts else None

        if isinstance(value, (list, tuple, set)):
            safe_items = []

            for item in value:
                safe_item = sqlite_safe(item)

                if safe_item is not None:
                    safe_items.append(str(safe_item))

            return ", ".join(safe_items) if safe_items else None

        # Last-resort conversion for custom objects.
        return str(value)

    # --------------------------------------------------------
    # CLEAN UPDATE VALUES
    # --------------------------------------------------------

    clean_updates = {}

    for key, value in updates.items():

        if key not in allowed:
            continue

        safe_value = sqlite_safe(value)

        if safe_value is not None:
            clean_updates[key] = safe_value

    # --------------------------------------------------------
    # NOTHING TO UPDATE
    # --------------------------------------------------------

    if not clean_updates:
        return get_hospital(hospital_id)

    # --------------------------------------------------------
    # BUILD UPDATE QUERY
    # --------------------------------------------------------

    sets = ", ".join(
        f"{key} = ?"
        for key in clean_updates
    )

    values = [
        sqlite_safe(value)
        for value in clean_updates.values()
    ]

    values.append(hospital_id)

    # Final safety check: no dictionary/list can reach sqlite3.
    for index, value in enumerate(values):
        if isinstance(value, (dict, list, tuple, set)):
            values[index] = str(value)

    # --------------------------------------------------------
    # UPDATE DATABASE
    # --------------------------------------------------------

    connection = get_connection()

    try:
        cursor = connection.execute(
            f"""
            UPDATE hospitals
            SET {sets}
            WHERE hospital_id = ?
            """,
            values
        )

        connection.commit()

        updated = cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    if updated:
        return get_hospital(hospital_id)

    return None

# ============================================================
# ATOMIC RESOURCE DECREMENT
# ============================================================
#
# This function prevents two simultaneous reservations from
# taking the same last available emergency resource.
#
# Example:
#
# ICU = 1
#
# Request A -> ICU becomes 0
# Request B -> UPDATE affects 0 rows -> reservation rejected
#
# ============================================================

def reserve_resource_atomically(
    hospital_id,
    resource
):

    allowed_resources = {

        "emergency_bed":
            "emergency_beds",

        "icu":
            "icu_available",

        "ventilator":
            "ventilator_available"
    }


    # --------------------------------------------------------
    # Check whether requested resource is supported
    # --------------------------------------------------------

    if resource not in allowed_resources:

        return False


    column = allowed_resources[resource]


    # --------------------------------------------------------
    # Open database connection
    # --------------------------------------------------------

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )


    try:

        cursor = connection.cursor()


        # ----------------------------------------------------
        # Begin immediate transaction
        #
        # SQLite obtains a write lock here.
        # This prevents another process from modifying the
        # same database between the availability check and
        # the update.
        # ----------------------------------------------------

        cursor.execute(
            "BEGIN IMMEDIATE"
        )


        # ----------------------------------------------------
        # Decrease resource only if it is still available
        # ----------------------------------------------------

        current_time = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        cursor.execute(
            f"""
            UPDATE hospitals

            SET {column} = {column} - 1,

                last_updated = ?

            WHERE hospital_id = ?

            AND {column} > 0
            """,

            (
                current_time,
                hospital_id
            )
        )


        # ----------------------------------------------------
        # rowcount == 1
        #
        # Resource was successfully reserved.
        # ----------------------------------------------------

        if cursor.rowcount == 1:

            connection.commit()

            return True


        # ----------------------------------------------------
        # rowcount == 0
        #
        # Hospital does not exist OR resource is already 0.
        # ----------------------------------------------------

        connection.rollback()

        return False


    except Exception:

        connection.rollback()

        raise


    finally:

        connection.close()


# ============================================================
# REGISTER NEW HOSPITAL
# ============================================================

def register_hospital(hospital_data):

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Generate next hospital ID
    # --------------------------------------------------------

    existing_ids = cursor.execute(
        """
        SELECT hospital_id
        FROM hospitals
        """
    ).fetchall()


    highest_number = 0


    for row in existing_ids:

        hospital_id = str(
            row["hospital_id"]
        )


        if hospital_id.startswith("H"):

            try:

                number = int(
                    hospital_id[1:]
                )


                if number > highest_number:

                    highest_number = number


            except ValueError:

                pass


    new_hospital_id = (

        "H"

        + str(
            highest_number + 1
        ).zfill(3)

    )


    # --------------------------------------------------------
    # Registration timestamp
    # --------------------------------------------------------

    registered_at = (

        hospital_data.get(
            "registered_at"
        )

        or

        pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    # --------------------------------------------------------
    # Insert hospital
    #
    # IMPORTANT:
    # New hospitals start as PENDING.
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO hospitals (

            hospital_id,

            hospital_name,

            hospital_type,

            latitude,

            longitude,

            emergency_beds,

            icu_total,

            icu_available,

            ventilator_available,

            oxygen_available,

            blood_available,

            trauma_care,

            cardiologist,

            neurologist,

            orthopedic,

            surgery,

            current_occupancy,

            last_updated,

            registration_number,

            contact_number,

            official_email,

            address,

            administrator_name,

            registration_status,

            registered_at

        )

        VALUES (

            ?, ?, ?, ?, ?, ?, ?, ?, ?,

            ?, ?, ?, ?, ?, ?, ?, ?, ?,

            ?, ?, ?, ?, ?, ?, ?

        )
        """,

        (

            new_hospital_id,

            hospital_data.get(
                "hospital_name",
                ""
            ),

            hospital_data.get(
                "hospital_type",
                "Private"
            ),

            float(
                hospital_data.get(
                    "latitude",
                    0
                )
            ),

            float(
                hospital_data.get(
                    "longitude",
                    0
                )
            ),

            int(
                hospital_data.get(
                    "emergency_beds",
                    0
                )
            ),

            int(
                hospital_data.get(
                    "icu_total",
                    0
                )
            ),

            int(
                hospital_data.get(
                    "icu_available",
                    0
                )
            ),

            int(
                hospital_data.get(
                    "ventilator_available",
                    0
                )
            ),

            hospital_data.get(
                "oxygen_available",
                "No"
            ),

            hospital_data.get(
                "blood_available",
                "No"
            ),

            hospital_data.get(
                "trauma_care",
                "No"
            ),

            hospital_data.get(
                "cardiologist",
                "No"
            ),

            hospital_data.get(
                "neurologist",
                "No"
            ),

            hospital_data.get(
                "orthopedic",
                "No"
            ),

            hospital_data.get(
                "surgery",
                "No"
            ),

            float(
                hospital_data.get(
                    "current_occupancy",
                    0
                )
            ),

            registered_at,

            hospital_data.get(
                "registration_number",
                ""
            ),

            hospital_data.get(
                "contact_number",
                ""
            ),

            hospital_data.get(
                "official_email",
                ""
            ),

            hospital_data.get(
                "address",
                ""
            ),

            hospital_data.get(
                "administrator_name",
                ""
            ),

            "PENDING",

            registered_at
        )
    )


    connection.commit()

    connection.close()


    return new_hospital_id


# ============================================================
# UPDATE HOSPITAL REGISTRATION STATUS
# ============================================================

def update_registration_status(
    hospital_id,
    status
):

    allowed_statuses = {

        "PENDING",

        "VERIFIED",

        "REJECTED"
    }


    status = status.upper()


    if status not in allowed_statuses:

        raise ValueError(
            "Invalid registration status. "
            "Use PENDING, VERIFIED or REJECTED."
        )


    connection = get_connection()


    cursor = connection.execute(
        """
        UPDATE hospitals

        SET registration_status = ?

        WHERE hospital_id = ?
        """,

        (
            status,
            hospital_id
        )
    )


    connection.commit()

    connection.close()


    if cursor.rowcount:

        return get_hospital(
            hospital_id
        )


    return None


# ============================================================
# AMBULANCE MANAGEMENT
# ============================================================


def get_all_ambulances():
    """Return all registered ambulances ordered by latest update."""

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM ambulances
            ORDER BY last_updated DESC, ambulance_id
            """
        ).fetchall()

    finally:

        connection.close()

    return [dict(row) for row in rows]


def get_available_ambulances():
    """Return ambulances that are currently available."""

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM ambulances
            WHERE status = 'AVAILABLE'
            ORDER BY last_updated DESC, ambulance_id
            """
        ).fetchall()

    finally:

        connection.close()

    return [dict(row) for row in rows]


def register_ambulance(
    ambulance_id,
    vehicle_number,
    driver_name,
    nurse_name,
    coordinator_name,
    latitude=None,
    longitude=None,
    status="AVAILABLE"
):
    """Register or update an ambulance."""

    if not ambulance_id:
        raise ValueError("ambulance_id is required")

    allowed_statuses = {
        "AVAILABLE",
        "ON_CALL",
        "EN_ROUTE",
        "IN_TRANSIT",
        "OFFLINE",
        "MAINTENANCE"
    }

    status = str(status or "AVAILABLE").upper()

    if status not in allowed_statuses:
        status = "AVAILABLE"

    current_time = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT OR REPLACE INTO ambulances (
                ambulance_id,
                vehicle_number,
                driver_name,
                nurse_name,
                coordinator_name,
                latitude,
                longitude,
                status,
                last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(ambulance_id),
                str(vehicle_number or ""),
                str(driver_name or ""),
                str(nurse_name or ""),
                str(coordinator_name or ""),
                latitude,
                longitude,
                status,
                current_time
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()

    return True


def update_ambulance_location(
    ambulance_id,
    latitude,
    longitude
):
    """Update an ambulance's latest GPS location."""

    current_time = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            UPDATE ambulances
            SET latitude = ?,
                longitude = ?,
                last_updated = ?
            WHERE ambulance_id = ?
            """,
            (
                latitude,
                longitude,
                current_time,
                str(ambulance_id)
            )
        )

        connection.commit()

        return cursor.rowcount == 1

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


def update_ambulance_status(
    ambulance_id,
    status
):
    """Update the operational status of an ambulance."""

    current_time = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    status = str(status or "AVAILABLE").upper()

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            UPDATE ambulances
            SET status = ?,
                last_updated = ?
            WHERE ambulance_id = ?
            """,
            (
                status,
                current_time,
                str(ambulance_id)
            )
        )

        connection.commit()

        return cursor.rowcount == 1

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


def assign_available_ambulance(
    latitude=None,
    longitude=None
):
    """
    Atomically assign the nearest available ambulance when
    coordinates are available. Otherwise assign the first
    available ambulance.
    """

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    try:

        cursor = connection.cursor()

        cursor.execute("BEGIN IMMEDIATE")

        rows = cursor.execute(
            """
            SELECT *
            FROM ambulances
            WHERE status = 'AVAILABLE'
            """
        ).fetchall()

        if not rows:
            connection.rollback()
            return None

        selected = None

        if latitude is not None and longitude is not None:

            try:

                target_lat = float(latitude)
                target_lon = float(longitude)

                def distance_squared(row):

                    if row["latitude"] is None or row["longitude"] is None:
                        return float("inf")

                    lat_diff = float(row["latitude"]) - target_lat
                    lon_diff = float(row["longitude"]) - target_lon

                    return (lat_diff * lat_diff) + (lon_diff * lon_diff)

                selected = min(
                    rows,
                    key=distance_squared
                )

            except (TypeError, ValueError):

                selected = None

        if selected is None:
            selected = rows[0]

        ambulance_id = selected["ambulance_id"]

        current_time = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            """
            UPDATE ambulances
            SET status = 'ON_CALL',
                last_updated = ?
            WHERE ambulance_id = ?
            AND status = 'AVAILABLE'
            """,
            (
                current_time,
                ambulance_id
            )
        )

        if cursor.rowcount != 1:
            connection.rollback()
            return None

        connection.commit()

        return dict(selected) | {
            "status": "ON_CALL",
            "last_updated": current_time
        }

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


def release_ambulance(
    ambulance_id
):
    """Release an ambulance back to AVAILABLE status."""

    return update_ambulance_status(
        ambulance_id,
        "AVAILABLE"
    )


# ============================================================
# CAPACITY SUMMARY
# ============================================================

def capacity_summary():

    connection = get_connection()


    rows = connection.execute(
        "SELECT * FROM hospitals"
    ).fetchall()


    connection.close()


    data = [
        dict(row)
        for row in rows
    ]


    return {

        "hospital_count":
            len(data),

        "emergency_beds_available":
            sum(
                int(
                    row["emergency_beds"]
                    or 0
                )
                for row in data
            ),

        "icu_available":
            sum(
                int(
                    row["icu_available"]
                    or 0
                )
                for row in data
            ),

        "ventilators_available":
            sum(
                int(
                    row["ventilator_available"]
                    or 0
                )
                for row in data
            ),

        "active_ambulances":
            get_count(
                "ambulances",
                "status IN "
                "('AVAILABLE','ON_CALL','IN_TRANSIT')"
            ),

        "active_emergencies":
            get_count(
                "reservations",
                "status IN "
                "('CONFIRMED',"
                "'IN_TRANSIT',"
                "'ARRIVED',"
                "'ADMITTED',"
                "'ON_CALL')"
            ),

        "active_reservations":
            get_count(
                "reservations",
                "status IN "
                "('CONFIRMED',"
                "'IN_TRANSIT',"
                "'ARRIVED',"
                "'ADMITTED',"
                "'ON_CALL')"
            )
    }


# ============================================================
# GENERIC COUNT FUNCTION
# ============================================================

def get_count(
    table,
    where="1=1"
):

    connection = get_connection()


    value = connection.execute(
        f"""
        SELECT COUNT(*)

        FROM {table}

        WHERE {where}
        """
    ).fetchone()[0]


    connection.close()


    return value
# =========================================================
# LIVE PATIENT ADMISSION / DISCHARGE
# =========================================================

def admit_patient(hospital_id, resource):
    """
    Admit a patient and reduce the selected available resource.
    Supported resources:
    emergency_bed, icu, ventilator
    """

    allowed_resources = {
        "emergency_bed": "emergency_beds",
        "icu": "icu_available",
        "ventilator": "ventilator_available"
    }

    if resource not in allowed_resources:
        return False

    column = allowed_resources[resource]

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    try:
        cursor = connection.cursor()

        current_time = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            f"""
            UPDATE hospitals
            SET {column} = {column} - 1,
                last_updated = ?
            WHERE hospital_id = ?
            AND {column} > 0
            """,
            (
                current_time,
                hospital_id
            )
        )

        if cursor.rowcount == 1:
            connection.commit()
            return True

        connection.rollback()
        return False

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def discharge_patient(hospital_id, resource):
    """
    Discharge a patient and increase the selected available resource.
    """

    allowed_resources = {
        "emergency_bed": "emergency_beds",
        "icu": "icu_available",
        "ventilator": "ventilator_available"
    }

    if resource not in allowed_resources:
        return False

    column = allowed_resources[resource]

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    try:
        cursor = connection.cursor()

        current_time = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            f"""
            UPDATE hospitals
            SET {column} = {column} + 1,
                last_updated = ?
            WHERE hospital_id = ?
            """,
            (
                current_time,
                hospital_id
            )
        )

        if cursor.rowcount == 1:
            connection.commit()
            return True

        connection.rollback()
        return False

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()