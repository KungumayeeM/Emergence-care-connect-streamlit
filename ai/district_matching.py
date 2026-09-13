import math
from pathlib import Path

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DISTRICT_FILE = BASE_DIR / "dataset" / "Districts.csv"


# ============================================================
# LOAD DISTRICT DATA
# ============================================================

def load_districts():

    districts = pd.read_csv(
        DISTRICT_FILE
    )

    return districts


# ============================================================
# HAVERSINE DISTANCE
# ============================================================
#
# Calculates the approximate distance between two
# geographical coordinates.
#
# Result is returned in kilometres.
# ============================================================

def calculate_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):

    earth_radius = 6371.0

    latitude1 = math.radians(
        latitude1
    )

    longitude1 = math.radians(
        longitude1
    )

    latitude2 = math.radians(
        latitude2
    )

    longitude2 = math.radians(
        longitude2
    )


    difference_latitude = (
        latitude2 - latitude1
    )

    difference_longitude = (
        longitude2 - longitude1
    )


    a = (
        math.sin(
            difference_latitude / 2
        ) ** 2
        +
        math.cos(latitude1)
        *
        math.cos(latitude2)
        *
        math.sin(
            difference_longitude / 2
        ) ** 2
    )


    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


    distance = (
        earth_radius * c
    )

    return distance


# ============================================================
# FIND NEAREST DISTRICT
# ============================================================

def get_district_from_coordinates(
    latitude,
    longitude
):

    districts = load_districts()

    nearest_district = None

    shortest_distance = float("inf")


    for _, district in districts.iterrows():

        distance = calculate_distance(

            latitude,

            longitude,

            float(district["latitude"]),

            float(district["longitude"])
        )


        if distance < shortest_distance:

            shortest_distance = distance

            nearest_district = district


    if nearest_district is None:

        return None


    return {

        "district_id":
            nearest_district["district_id"],

        "district_name":
            nearest_district["district_name"],

        "state":
            nearest_district["state"],

        "distance_km":
            round(
                shortest_distance,
                2
            )
    }


# ============================================================
# GET HOSPITAL DISTRICT
# ============================================================
#
# Determines which district a hospital belongs to based
# on its latitude and longitude.
# ============================================================

def get_hospital_district(
    hospital
):

    latitude = float(
        hospital["latitude"]
    )

    longitude = float(
        hospital["longitude"]
    )


    return get_district_from_coordinates(
        latitude,
        longitude
    )


# ============================================================
# ADD DISTRICT INFORMATION TO HOSPITALS
# ============================================================

def add_district_to_hospitals(
    hospitals
):

    updated_hospitals = []


    for hospital in hospitals:

        hospital_copy = hospital.copy()

        district = get_hospital_district(
            hospital
        )


        if district:

            hospital_copy["district_id"] = (
                district["district_id"]
            )

            hospital_copy["district_name"] = (
                district["district_name"]
            )

            hospital_copy["district_distance_km"] = (
                district["distance_km"]
            )

        else:

            hospital_copy["district_id"] = None

            hospital_copy["district_name"] = None

            hospital_copy["district_distance_km"] = None


        updated_hospitals.append(
            hospital_copy
        )


    return updated_hospitals


# ============================================================
# GET HOSPITALS IN PATIENT'S DISTRICT
# ============================================================

def get_hospitals_by_district(
    hospitals,
    patient_latitude,
    patient_longitude
):

    patient_district = get_district_from_coordinates(

        patient_latitude,

        patient_longitude
    )


    if patient_district is None:

        return [], None


    hospitals_with_district = (
        add_district_to_hospitals(
            hospitals
        )
    )


    district_hospitals = [

        hospital

        for hospital in hospitals_with_district

        if hospital["district_id"]
        == patient_district["district_id"]
    ]


    return (
        district_hospitals,
        patient_district
    )


# ============================================================
# GET VERIFIED HOSPITALS IN PATIENT'S DISTRICT
# ============================================================

def get_verified_hospitals_by_district(
    hospitals,
    patient_latitude,
    patient_longitude
):

    verified_hospitals = [

        hospital

        for hospital in hospitals

        if hospital.get(
            "registration_status"
        ) == "VERIFIED"
    ]


    return get_hospitals_by_district(

        verified_hospitals,

        patient_latitude,

        patient_longitude
    )


# ============================================================
# FIND NEAREST DISTRICTS
# ============================================================

def get_nearest_districts(
    latitude,
    longitude,
    number_of_districts=3
):

    districts = load_districts()

    district_results = []


    for _, district in districts.iterrows():

        distance = calculate_distance(

            latitude,

            longitude,

            float(district["latitude"]),

            float(district["longitude"])
        )


        district_results.append({

            "district_id":
                district["district_id"],

            "district_name":
                district["district_name"],

            "state":
                district["state"],

            "distance_km":
                round(
                    distance,
                    2
                )
        })


    district_results.sort(
        key=lambda item:
            item["distance_km"]
    )


    return district_results[
        :number_of_districts
    ]


# ============================================================
# FIND DISTRICT AND HOSPITAL INFORMATION
# ============================================================

def get_district_summary(
    hospitals,
    latitude,
    longitude
):

    district = get_district_from_coordinates(

        latitude,

        longitude
    )


    if district is None:

        return {

            "patient_district": None,

            "hospital_count": 0,

            "hospitals": []
        }


    hospitals_with_district = (
        add_district_to_hospitals(
            hospitals
        )
    )


    district_hospitals = [

        hospital

        for hospital
        in hospitals_with_district

        if hospital["district_id"]
        == district["district_id"]
    ]


    return {

        "patient_district":
            district,

        "hospital_count":
            len(district_hospitals),

        "hospitals":
            district_hospitals
    }