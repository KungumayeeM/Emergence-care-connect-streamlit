import hashlib
import hmac
import sqlite3
from pathlib import Path

import streamlit as st


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "Backend" / "emergencycare.db"


# ---------------------------------------------------------
# ROLE PERMISSIONS
# ---------------------------------------------------------

ROLE_PERMISSIONS = {
    "Patient Attendant": [
        "patient_app"
    ],

    "Ambulance Monitor": [
        "ambulance_monitor"
    ],

    "Hospital Staff": [
        "hospital_capacity"
    ],

    "Authority": [
        "hospital_dashboard",
        "hospital_registration",
        "admin_verification",
        "ambulance_monitor",
        "authority_dashboard"
    ]
}


# ---------------------------------------------------------
# DEMO ACCOUNTS
# ---------------------------------------------------------

DEMO_USERS = {
    "patient": {
        "password": "patient123",
        "name": "Demo Patient Attendant",
        "role": "Patient Attendant"
    },

    "ambulance": {
        "password": "ambulance123",
        "name": "Demo Ambulance Monitor",
        "role": "Ambulance Monitor"
    },

    "hospital": {
        "password": "hospital123",
        "name": "Demo Hospital Staff",
        "role": "Hospital Staff"
    },

    "authority": {
        "password": "authority123",
        "name": "Demo Authority",
        "role": "Authority"
    }
}


# ---------------------------------------------------------
# PASSWORD FUNCTIONS
# ---------------------------------------------------------

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verify_password(password, password_hash):

    return hmac.compare_digest(
        hash_password(password),
        password_hash
    )


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------------
# INITIALIZE AUTH DATABASE
# ---------------------------------------------------------

def initialize_auth():

    DATABASE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            account_status TEXT DEFAULT 'ACTIVE',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()


    # -----------------------------------------------------
    # CREATE DEMO ACCOUNTS
    # -----------------------------------------------------

    for username, user_data in DEMO_USERS.items():

        existing_user = cursor.execute(
            """
            SELECT username
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if existing_user is None:

            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    password_hash,
                    full_name,
                    role,
                    account_status
                )
                VALUES (?, ?, ?, ?, 'ACTIVE')
                """,
                (
                    username,
                    hash_password(
                        user_data["password"]
                    ),
                    user_data["name"],
                    user_data["role"]
                )
            )

    connection.commit()

    connection.close()


# ---------------------------------------------------------
# PATIENT SIGN UP
# ---------------------------------------------------------

def register_patient(
    full_name,
    username,
    password
):

    full_name = full_name.strip()

    username = username.strip().lower()

    password = password.strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if full_name == "":

        return {
            "success": False,
            "message": "Please enter your full name."
        }


    if len(full_name) < 2:

        return {
            "success": False,
            "message": "Please enter a valid full name."
        }


    if username == "":

        return {
            "success": False,
            "message": "Please choose a username."
        }


    if len(username) < 4:

        return {
            "success": False,
            "message": (
                "Username must contain at least "
                "4 characters."
            )
        }


    if " " in username:

        return {
            "success": False,
            "message": (
                "Username cannot contain spaces."
            )
        }


    if password == "":

        return {
            "success": False,
            "message": "Please enter a password."
        }


    if len(password) < 6:

        return {
            "success": False,
            "message": (
                "Password must contain at least "
                "6 characters."
            )
        }


    # -----------------------------------------------------
    # CHECK EXISTING USER
    # -----------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    existing_user = cursor.execute(
        """
        SELECT username
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    if existing_user is not None:

        connection.close()

        return {
            "success": False,
            "message": (
                "Username already exists. "
                "Please choose another username."
            )
        }


    # -----------------------------------------------------
    # CREATE PATIENT ACCOUNT
    # -----------------------------------------------------

    cursor.execute(
        """
        INSERT INTO users (
            username,
            password_hash,
            full_name,
            role,
            account_status
        )
        VALUES (
            ?,
            ?,
            ?,
            'Patient Attendant',
            'ACTIVE'
        )
        """,
        (
            username,
            hash_password(password),
            full_name
        )
    )


    connection.commit()

    connection.close()


    return {
        "success": True,
        "message": (
            "Patient Attendant account "
            "created successfully."
        )
    }


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

def login(
    username,
    password
):

    username = username.strip().lower()


    # Make sure users table exists.
    initialize_auth()


    connection = get_connection()

    user = connection.execute(
        """
        SELECT
            username,
            password_hash,
            full_name,
            role,
            account_status
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    connection.close()


    # -----------------------------------------------------
    # ACCOUNT NOT FOUND
    # -----------------------------------------------------

    if user is None:

        return {
            "success": False,
            "message": (
                "Account not found. "
                "Please use the Sign Up tab "
                "to create a Patient Attendant account."
            )
        }


    # -----------------------------------------------------
    # ACCOUNT STATUS
    # -----------------------------------------------------

    if user["account_status"] != "ACTIVE":

        return {
            "success": False,
            "message": (
                "This account is not active."
            )
        }


    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    if not verify_password(
        password,
        user["password_hash"]
    ):

        return {
            "success": False,
            "message": "Incorrect password."
        }


    # -----------------------------------------------------
    # SAVE LOGIN SESSION
    # -----------------------------------------------------

    st.session_state.logged_in = True

    st.session_state.username = user["username"]

    st.session_state.full_name = user["full_name"]

    st.session_state.role = user["role"]


    return {
        "success": True,
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"]
    }


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

def logout():

    auth_keys = [
        "logged_in",
        "username",
        "full_name",
        "role"
    ]


    for key in auth_keys:

        if key in st.session_state:

            del st.session_state[key]


    st.rerun()


# ---------------------------------------------------------
# LOGIN STATE
# ---------------------------------------------------------

def is_logged_in():

    return st.session_state.get(
        "logged_in",
        False
    )


def get_current_user():

    return st.session_state.get(
        "username",
        None
    )


def get_current_full_name():

    return st.session_state.get(
        "full_name",
        None
    )


def get_current_role():

    return st.session_state.get(
        "role",
        None
    )


# ---------------------------------------------------------
# PERMISSION CHECK
# ---------------------------------------------------------

def has_permission(permission):

    role = get_current_role()

    if role is None:

        return False


    return permission in ROLE_PERMISSIONS.get(
        role,
        []
    )


def require_login():

    if not is_logged_in():

        show_login_page()

        st.stop()


def require_role(required_role):

    require_login()

    current_role = get_current_role()


    if current_role != required_role:

        st.error(
            "⛔ Access denied. "
            "This module is available only to "
            + required_role
            + "."
        )

        st.stop()


def require_permission(permission):

    require_login()


    if not has_permission(permission):

        st.error(
            "⛔ You do not have permission "
            "to access this module."
        )

        st.stop()


# ---------------------------------------------------------
# SIDEBAR USER INFORMATION
# ---------------------------------------------------------

def display_user_info():

    if not is_logged_in():

        return


    st.sidebar.success(
        "Logged in as: "
        + str(
            get_current_full_name()
        )
    )


    st.sidebar.caption(
        "Username: "
        + str(
            get_current_user()
        )
    )


    st.sidebar.caption(
        "Role: "
        + str(
            get_current_role()
        )
    )


def logout_button():

    if is_logged_in():

        if st.sidebar.button(
            "🚪 Logout",
            use_container_width=True
        ):

            logout()


# ---------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------

def show_login_page():

    st.title(
        "🔐 EmergencyCare Connect"
    )

    st.subheader(
        "Secure Role-Based Access"
    )

    st.write(
        "Login to access EmergencyCare Connect."
    )

    st.divider()


    # -----------------------------------------------------
    # LOGIN / SIGN UP TABS
    # -----------------------------------------------------

    login_tab, signup_tab = st.tabs(
        [
            "🔑 Login",
            "📝 Sign Up"
        ]
    )


    # =====================================================
    # LOGIN TAB
    # =====================================================

    with login_tab:

        st.subheader(
            "Login"
        )


        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username"
        )


        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )


        login_button = st.button(
            "Login",
            type="primary",
            use_container_width=True,
            key="login_button"
        )


        if login_button:

            if username.strip() == "":

                st.error(
                    "Please enter your username."
                )


            elif password == "":

                st.error(
                    "Please enter your password."
                )


            else:

                result = login(
                    username,
                    password
                )


                if result["success"]:

                    st.success(
                        "Login successful."
                    )

                    st.rerun()

                else:

                    st.error(
                        result["message"]
                    )


    # =====================================================
    # SIGN UP TAB
    # =====================================================

    with signup_tab:

        st.subheader(
            "Create Patient Attendant Account"
        )


        st.info(
            "Public sign-up is available only "
            "for Patient Attendant accounts."
        )


        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
            key="signup_full_name"
        )


        new_username = st.text_input(
            "Username",
            placeholder="Choose a username",
            key="signup_username"
        )


        new_password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters",
            key="signup_password"
        )


        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
            key="signup_confirm_password"
        )


        signup_button = st.button(
            "Create Account",
            type="primary",
            use_container_width=True,
            key="signup_button"
        )


        if signup_button:

            if new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                result = register_patient(
                    full_name,
                    new_username,
                    new_password
                )


                if result["success"]:

                    st.success(
                        result["message"]
                    )

                    st.info(
                        "Now open the Login tab "
                        "and login using your new account."
                    )

                else:

                    st.error(
                        result["message"]
                    )


    # =====================================================
    # DEMO ACCOUNTS
    # =====================================================

    st.divider()

    st.subheader(
        "Demo Access"
    )


    st.info(
        "Patient Attendant: "
        "patient / patient123\n\n"
        "Ambulance Monitor: "
        "ambulance / ambulance123\n\n"
        "Hospital Staff: "
        "hospital / hospital123\n\n"
        "Authority: "
        "authority / authority123"
    )


    st.caption(
        "For this prototype, public Sign Up creates "
        "Patient Attendant accounts only."
    )


# ---------------------------------------------------------
# ROLE HOME
# ---------------------------------------------------------

def show_role_home():

    role = get_current_role()


    if role == "Patient Attendant":

        st.title(
            "🚑 EmergencyCare Connect"
        )


    elif role == "Ambulance Monitor":

        st.title(
            "🚑 Ambulance Monitor"
        )


    elif role == "Hospital Staff":

        st.title(
            "🏥 Hospital Capacity Module"
        )


    elif role == "Authority":

        st.title(
            "🏛️ Authority Control Center"
        )