from datetime import datetime
from typing import Optional
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel, Field, EmailStr

from Backend.database import (
    get_all_hospitals,
    get_hospital,
    update_hospital_capacity,
    capacity_summary,
    get_connection,
    initialize_database
)

from Backend.auth import (
    create_user,
    authenticate_user,
    get_user
)

from Backend.reservation import (
    create_reservation,
    confirm_reservation,
    get_reservation,
    get_reservations,
    start_patient_transport,
    mark_patient_arrived,
    admit_patient,
    cancel_reservation,
    expire_reservations
)

from ai.hospital_matching import match_hospitals


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="EmergencyCare Connect API",
    version="3.0",
    description="AI-powered emergency hospital matching and reservation platform"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# AUTHENTICATION MODELS
# ============================================================

class SignupRequest(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    phone: str = Field(
        min_length=10,
        max_length=15
    )

    password: str = Field(
        min_length=6,
        max_length=100
    )

    role: str = "PATIENT"


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# ============================================================
# PATIENT MODEL
# ============================================================

class PatientRequest(BaseModel):

    name: str = "Emergency Patient"

    age: Optional[int] = None

    gender: Optional[str] = None

    contact: Optional[str] = None

    blood_group: Optional[str] = None

    allergies: Optional[str] = None

    existing_conditions: Optional[str] = None

    medication: Optional[str] = None

    emergency_type: str = "Other"

    consciousness: str = "Conscious"

    breathing: str = "Normal"

    bleeding: str = "None"

    severity: str = "Serious"

    required_resources: list[str] = Field(
        default_factory=lambda: ["emergency_bed"]
    )

    specialist: str = ""

    latitude: float

    longitude: float


# ============================================================
# CAPACITY MODEL
# ============================================================

class CapacityUpdate(BaseModel):

    emergency_beds: Optional[int] = None

    icu_available: Optional[int] = None

    ventilator_available: Optional[int] = None

    oxygen_available: Optional[str] = None

    blood_available: Optional[str] = None

    trauma_care: Optional[str] = None

    cardiologist: Optional[str] = None

    neurologist: Optional[str] = None

    orthopedic: Optional[str] = None

    surgery: Optional[str] = None

    current_occupancy: Optional[float] = None


# ============================================================
# RESERVATION MODEL
# ============================================================

class ReservationRequest(BaseModel):

    hospital_id: str

    hospital_name: str

    patient_name: str

    required_resources: list[str] = Field(
        default_factory=lambda: ["emergency_bed"]
    )

    patient_id: Optional[str] = None


# ============================================================
# AMBULANCE MODEL
# ============================================================

class AmbulanceRequest(BaseModel):

    ambulance_id: Optional[str] = None

    vehicle_number: str

    driver_name: str

    nurse_name: str

    coordinator_name: str

    latitude: float

    longitude: float

    status: str = "AVAILABLE"


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def home():

    return {
        "message": "EmergencyCare Connect API is running",
        "version": "3.0"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "database": "connected"
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/auth/signup")
def signup(request: SignupRequest):

    role = request.role.upper()

    allowed_roles = [
        "PATIENT",
        "HOSPITAL",
        "ADMIN"
    ]

    if role not in allowed_roles:

        role = "PATIENT"

    user, error = create_user(
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
        password=request.password,
        role=role
    )

    if error:

        raise HTTPException(
            status_code=400,
            detail=error
        )

    return {
        "status": "success",
        "message": "Account created successfully",
        "user": user
    }


@app.post("/auth/login")
def login(request: LoginRequest):

    user = authenticate_user(
        email=request.email,
        password=request.password
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "status": "success",
        "message": "Login successful",
        "user": user
    }


@app.get("/auth/user/{user_id}")
def user_profile(user_id: int):

    user = get_user(user_id)

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "status": "success",
        "user": user
    }


# ============================================================
# HOSPITALS
# ============================================================

@app.get("/hospitals")
def hospitals():

    return {
        "status": "success",
        "hospitals": get_all_hospitals()
    }


@app.get("/hospitals/{hospital_id}")
def hospital(hospital_id: str):

    h = get_hospital(hospital_id)

    if not h:

        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    return {
        "status": "success",
        "hospital": h
    }


@app.get("/hospitals/{hospital_id}/capacity")
def hospital_capacity(hospital_id: str):

    h = get_hospital(hospital_id)

    if not h:

        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    return {
        "hospital_id": hospital_id,
        "hospital_name": h["hospital_name"],
        "emergency_beds": h["emergency_beds"],
        "icu_total": h["icu_total"],
        "icu_available": h["icu_available"],
        "ventilator_available": h["ventilator_available"],
        "oxygen_available": h["oxygen_available"],
        "blood_available": h["blood_available"],
        "occupancy": h["current_occupancy"],
        "last_updated": h["last_updated"]
    }


@app.put("/hospitals/{hospital_id}/capacity")
def update_capacity(
    hospital_id: str,
    request: CapacityUpdate
):

    data = request.model_dump(
        exclude_none=True
    )

    data["last_updated"] = datetime.now().isoformat(
        timespec="seconds"
    )

    h = update_hospital_capacity(
        hospital_id,
        data
    )

    if not h:

        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    return {
        "status": "success",
        "hospital": h
    }


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get("/dashboard/summary")
def dashboard_summary():

    expire_reservations()

    return {
        "status": "success",
        "summary": capacity_summary()
    }


# ============================================================
# PATIENT
# ============================================================

@app.post("/patients")
def create_patient(request: PatientRequest):

    patient_id = (
        "PAT-" +
        str(uuid.uuid4())[:8].upper()
    )

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO patients
        VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
        """,
        (
            patient_id,
            request.name,
            request.age,
            request.gender,
            request.contact,
            request.blood_group,
            request.allergies,
            request.existing_conditions,
            request.medication,
            request.emergency_type,
            request.consciousness,
            request.breathing,
            request.bleeding,
            request.severity,
            ",".join(request.required_resources),
            request.latitude,
            request.longitude,
            now
        )
    )

    connection.commit()

    connection.close()

    return {
        "status": "success",
        "patient_id": patient_id
    }


# ============================================================
# AI HOSPITAL MATCHING
# ============================================================

@app.post("/match-hospitals")
def match_patient(request: PatientRequest):

    patient = request.model_dump()

    results = match_hospitals(
        patient,
        {
            "latitude": request.latitude,
            "longitude": request.longitude
        }
    )

    return {
        "status": "success",
        "recommended_hospital": (
            results[0]
            if results
            else None
        ),
        "ranked_hospitals": results
    }


# ============================================================
# RESERVATION
# ============================================================

@app.post("/reserve")
def reserve_hospital(
    request: ReservationRequest
):

    if not get_hospital(
        request.hospital_id
    ):

        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    reservation = create_reservation(
        request.hospital_id,
        request.hospital_name,
        request.patient_name,
        ",".join(
            request.required_resources
        ),
        request.patient_id,
        request.required_resources
    )

    return {
        "status": "success",
        "message": "Reservation request sent to hospital",
        "reservation": reservation
    }


@app.post("/reservations/{reservation_id}/confirm")
def confirm(reservation_id: str):

    reservation = confirm_reservation(
        reservation_id
    )

    if not reservation:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return {
        "status": "success",
        "reservation": reservation
    }


@app.get("/reservations")
def reservations():

    return {
        "status": "success",
        "reservations": get_reservations()
    }


@app.get("/reservations/{reservation_id}")
def reservation(
    reservation_id: str
):

    reservation_data = get_reservation(
        reservation_id
    )

    if not reservation_data:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return {
        "status": "success",
        "reservation": reservation_data
    }


@app.post("/reservations/{reservation_id}/transport")
def transport(
    reservation_id: str
):

    reservation_data = start_patient_transport(
        reservation_id
    )

    if not reservation_data:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found or invalid status"
        )

    return {
        "status": "success",
        "reservation": reservation_data
    }


@app.post("/reservations/{reservation_id}/arrive")
def arrive(
    reservation_id: str
):

    reservation_data = mark_patient_arrived(
        reservation_id
    )

    if not reservation_data:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found or invalid status"
        )

    return {
        "status": "success",
        "reservation": reservation_data
    }


@app.post("/reservations/{reservation_id}/admit")
def admit(
    reservation_id: str
):

    reservation_data = admit_patient(
        reservation_id
    )

    if not reservation_data:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found or invalid status"
        )

    return {
        "status": "success",
        "reservation": reservation_data
    }


@app.post("/reservations/{reservation_id}/cancel")
def cancel(
    reservation_id: str
):

    reservation_data = cancel_reservation(
        reservation_id
    )

    if not reservation_data:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return {
        "status": "success",
        "reservation": reservation_data
    }


@app.post("/reservations/expire")
def expire():

    return {
        "status": "success",
        "expired": expire_reservations()
    }


# ============================================================
# DYNAMIC FALLBACK
# ============================================================

@app.post("/reservations/{reservation_id}/fallback")
def fallback(
    reservation_id: str,
    latitude: float,
    longitude: float
):

    old = get_reservation(
        reservation_id
    )

    if not old:

        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    if old["status"] not in (
        "RESERVED",
        "PATIENT_IN_TRANSIT"
    ):

        raise HTTPException(
            status_code=400,
            detail="Fallback is available only for an active reservation"
        )

    patient = {
        "required_resources":
            old["required_resources"],
        "specialist": ""
    }

    candidates = match_hospitals(
        patient,
        {
            "latitude": latitude,
            "longitude": longitude
        },
        {
            old["hospital_id"]
        }
    )

    eligible = [
        x
        for x in candidates
        if x["eligible"]
    ]

    if not eligible:

        raise HTTPException(
            status_code=409,
            detail="No alternative hospital currently satisfies the requested resources"
        )

    cancel_reservation(
        reservation_id
    )

    new_reservation = create_reservation(
        eligible[0]["hospital_id"],
        eligible[0]["hospital_name"],
        old["patient_name"],
        ",".join(
            old["required_resources"]
        ),
        old["patient_id"],
        old["required_resources"]
    )

    return {
        "status": "success",
        "message": "Dynamic fallback selected an alternative hospital",
        "previous_reservation": old,
        "alternative_hospital": eligible[0],
        "new_reservation": new_reservation
    }


# ============================================================
# TRANSFERS
# ============================================================

@app.post("/transfers")
def create_transfer(
    patient_id: str,
    source_hospital_id: str,
    destination_hospital_id: str
):

    transfer_id = (
        "TRN-" +
        str(uuid.uuid4())[:8].upper()
    )

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO transfers
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transfer_id,
            patient_id,
            source_hospital_id,
            destination_hospital_id,
            "REQUESTED",
            now,
            None
        )
    )

    connection.commit()

    connection.close()

    return {
        "status": "success",
        "transfer_id": transfer_id,
        "status_value": "REQUESTED"
    }


@app.get("/transfers")
def transfers():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM transfers
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return {
        "status": "success",
        "transfers": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# AMBULANCES
# ============================================================

@app.post("/ambulances")
def register_ambulance(
    request: AmbulanceRequest
):

    ambulance_id = (
        request.ambulance_id
        or
        "AMB-" +
        str(uuid.uuid4())[:8].upper()
    )

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO ambulances
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ambulance_id,
            request.vehicle_number,
            request.driver_name,
            request.nurse_name,
            request.coordinator_name,
            request.latitude,
            request.longitude,
            request.status,
            now
        )
    )

    connection.commit()

    connection.close()

    return {
        "status": "success",
        "ambulance_id": ambulance_id
    }


@app.get("/ambulances")
def ambulances():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM ambulances
        ORDER BY last_updated DESC
        """
    ).fetchall()

    connection.close()

    return {
        "status": "success",
        "ambulances": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/app",
    StaticFiles(
        directory="Frontend",
        html=True
    ),
    name="frontend"
)


@app.get("/login")
def login_page():

    return FileResponse(
        "Frontend/login.html"
    )


@app.get("/signup")
def signup_page():

    return FileResponse(
        "Frontend/signup.html"
    )


@app.get("/dashboard")
def dashboard():

    return FileResponse(
        "Frontend/index.html"
    )