import math
from datetime import datetime

from Backend.database import get_all_hospitals

from ai.district_matching import (
    get_district_from_coordinates,
    get_hospital_district,
    get_nearest_districts
)


SPECIALISTS = {
    'cardiologist',
    'neurologist',
    'orthopedic'
}


def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0

    p1 = math.radians(float(lat1))
    p2 = math.radians(float(lat2))

    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


def freshness_minutes(timestamp):
    if not timestamp:
        return 9999

    try:
        dt = datetime.fromisoformat(str(timestamp))

        return max(
            0,
            (datetime.now() - dt).total_seconds() / 60
        )

    except ValueError:
        return 9999


def calculate_hospital_result(
    patient,
    ambulance_location,
    hospital,
    patient_district_name
):
    """
    Calculate the hospital result using the existing
    scoring algorithm.

    The scoring values are intentionally unchanged.
    """

    required = set(
        patient.get('required_resources', [])
    )

    specialist = patient.get('specialist', '')

    if specialist in SPECIALISTS:
        required.add(specialist)

    score = 0

    reasons = []
    unavailable = []

    # ---------------------------------------------------------
    # CLINICAL / RESOURCE FIT
    # Existing scoring values preserved
    # ---------------------------------------------------------

    checks = [
        (
            'emergency_bed',
            int(hospital['emergency_beds']) > 0,
            15,
            'Emergency bed'
        ),

        (
            'icu',
            int(hospital['icu_available']) > 0,
            15,
            'ICU'
        ),

        (
            'ventilator',
            int(hospital['ventilator_available']) > 0,
            12,
            'Ventilator'
        ),

        (
            'oxygen',
            hospital['oxygen_available'] == 'Yes',
            8,
            'Oxygen'
        ),

        (
            'blood',
            hospital['blood_available'] == 'Yes',
            8,
            'Blood'
        ),

        (
            'trauma',
            hospital['trauma_care'] == 'Yes',
            7,
            'Trauma care'
        ),

        (
            'cardiologist',
            hospital['cardiologist'] == 'Yes',
            5,
            'Cardiologist'
        ),

        (
            'neurologist',
            hospital['neurologist'] == 'Yes',
            5,
            'Neurologist'
        ),

        (
            'orthopedic',
            hospital['orthopedic'] == 'Yes',
            5,
            'Orthopedic specialist'
        ),

        (
            'surgery',
            hospital['surgery'] == 'Yes',
            5,
            'Surgery'
        )
    ]

    for key, available, points, label in checks:

        if key not in required:
            continue

        if available:
            score += points
            reasons.append(
                label + ' available'
            )

        else:
            unavailable.append(label)

            reasons.append(
                label + ' unavailable'
            )

    # ---------------------------------------------------------
    # DISTANCE
    # Existing calculation preserved
    # ---------------------------------------------------------

    distance = calculate_distance(
        ambulance_location['latitude'],
        ambulance_location['longitude'],
        hospital['latitude'],
        hospital['longitude']
    )

    # ---------------------------------------------------------
    # ETA
    # Existing calculation preserved
    # ---------------------------------------------------------

    eta_minutes = (distance / 30) * 60

    # ---------------------------------------------------------
    # DATA FRESHNESS
    # Existing calculation preserved
    # ---------------------------------------------------------

    fresh = freshness_minutes(
        hospital['last_updated']
    )

    # ---------------------------------------------------------
    # TRANSPORT / OPERATIONAL SCORE
    # Existing scoring preserved
    #
    # Distance = 8 / 5 / 2
    # ETA      = 6 / 4 / 2
    # Freshness = 6 / 3 / 1
    # ---------------------------------------------------------

    score += (
        8
        if distance <= 5
        else 5
        if distance <= 10
        else 2
    )

    score += (
        6
        if eta_minutes <= 10
        else 4
        if eta_minutes <= 20
        else 2
    )

    score += (
        6
        if fresh <= 5
        else 3
        if fresh <= 30
        else 1
    )

    if fresh > 30:
        reasons.append(
            'Capacity data is stale'
        )

    else:
        reasons.append(
            'Capacity data is recent'
        )

    # ---------------------------------------------------------
    # ELIGIBILITY
    # Existing eligibility logic preserved
    # ---------------------------------------------------------

    eligible = len(unavailable) == 0

    if not eligible:

        reasons.append(
            'Not fully suitable for requested resources'
        )

    else:

        reasons.append(
            'All requested resources currently available'
        )

    # ---------------------------------------------------------
    # HOSPITAL DISTRICT
    # ---------------------------------------------------------

    hospital_district = get_hospital_district(
        hospital
    )

    hospital_district_name = (
        hospital_district['district_name']
        if hospital_district
        else 'Unknown'
    )

    # ---------------------------------------------------------
    # DISTRICT MATCH INFORMATION
    # ---------------------------------------------------------

    if (
        patient_district_name
        and hospital_district_name
        == patient_district_name
    ):

        district_match = 'Same district'
        district_priority = 0

    else:

        district_match = (
            'Nearby district: '
            + hospital_district_name
        )

        district_priority = 1

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    return {
        'hospital_id': hospital['hospital_id'],

        'hospital_name': hospital['hospital_name'],

        'hospital_type': hospital['hospital_type'],

        'district': hospital_district_name,

        'district_match': district_match,

        'district_priority': district_priority,

        'distance_km': round(distance, 2),

        'estimated_eta_minutes': round(eta_minutes),

        'capacity_freshness_minutes': round(
            fresh,
            1
        ),

        'current_occupancy': hospital[
            'current_occupancy'
        ],

        'suitability_score': min(
            100,
            round(score)
        ),

        'eligible': eligible,

        'unavailable_requirements': unavailable,

        'reasons': reasons
    }


def rank_results(results):
    """
    Preserve the existing ranking logic.

    Eligible hospitals are ranked first,
    followed by suitability score and distance.

    District priority is used only as an additional
    tie-breaker for hospitals from the same search stage.
    """

    results.sort(
        key=lambda x: (
            not x['eligible'],
            -x['suitability_score'],
            x['distance_km']
        )
    )

    return results


def match_hospitals(
    patient,
    ambulance_location,
    exclude_hospital_ids=None
):
    """
    District-aware hospital matching.

    STAGE 1:
        Search verified hospitals in the patient's district.

    STAGE 2:
        If Stage 1 has NO eligible hospital,
        search verified hospitals in the nearest districts.

    The existing hospital scoring algorithm is preserved.
    """

    exclude_hospital_ids = set(
        exclude_hospital_ids or []
    )

    # ---------------------------------------------------------
    # GET ONLY VERIFIED HOSPITALS
    # ---------------------------------------------------------

    hospitals = get_all_hospitals(
        verified_only=True
    )

    # ---------------------------------------------------------
    # DETERMINE PATIENT DISTRICT
    # ---------------------------------------------------------

    patient_latitude = ambulance_location[
        'latitude'
    ]

    patient_longitude = ambulance_location[
        'longitude'
    ]

    patient_district = get_district_from_coordinates(
        patient_latitude,
        patient_longitude
    )

    if patient_district:

        patient_district_name = patient_district[
            'district_name'
        ]

    else:

        patient_district_name = None

    # ---------------------------------------------------------
    # REMOVE EXCLUDED HOSPITALS
    # ---------------------------------------------------------

    available_hospitals = [
        hospital
        for hospital in hospitals
        if hospital['hospital_id']
        not in exclude_hospital_ids
    ]

    # ---------------------------------------------------------
    # STAGE 1
    #
    # Search hospitals in patient's district
    # ---------------------------------------------------------

    same_district_hospitals = []

    if patient_district_name:

        for hospital in available_hospitals:

            hospital_district = get_hospital_district(
                hospital
            )

            if not hospital_district:
                continue

            if (
                hospital_district['district_name']
                == patient_district_name
            ):

                same_district_hospitals.append(
                    hospital
                )

    stage_1_results = []

    for hospital in same_district_hospitals:

        result = calculate_hospital_result(
            patient,
            ambulance_location,
            hospital,
            patient_district_name
        )

        stage_1_results.append(result)

    rank_results(stage_1_results)

    # ---------------------------------------------------------
    # CHECK WHETHER STAGE 1 HAS AN ELIGIBLE HOSPITAL
    # ---------------------------------------------------------

    stage_1_eligible = [
        result
        for result in stage_1_results
        if result['eligible']
    ]

    # ---------------------------------------------------------
    # STAGE 1 SUCCESS
    #
    # If at least one suitable hospital exists in the
    # patient's district, DO NOT expand to another district.
    # ---------------------------------------------------------

    if stage_1_eligible:

        return stage_1_results

    # ---------------------------------------------------------
    # STAGE 2
    #
    # No suitable hospital in patient's district.
    # Search nearest districts.
    # ---------------------------------------------------------

    nearest_districts = get_nearest_districts(
        patient_latitude,
        patient_longitude,
        4
    )

    stage_2_results = []

    for district in nearest_districts:

        district_name = district[
            'district_name'
        ]

        # Skip patient's own district.
        if (
            patient_district_name
            and district_name
            == patient_district_name
        ):
            continue

        district_hospitals = []

        for hospital in available_hospitals:

            hospital_district = get_hospital_district(
                hospital
            )

            if not hospital_district:
                continue

            if (
                hospital_district['district_name']
                == district_name
            ):

                district_hospitals.append(
                    hospital
                )

        if not district_hospitals:
            continue

        current_district_results = []

        for hospital in district_hospitals:

            result = calculate_hospital_result(
                patient,
                ambulance_location,
                hospital,
                patient_district_name
            )

            current_district_results.append(
                result
            )

        rank_results(
            current_district_results
        )

        # -----------------------------------------------------
        # CHECK THIS NEARBY DISTRICT
        # -----------------------------------------------------

        current_eligible = [
            result
            for result in current_district_results
            if result['eligible']
        ]

        if current_eligible:

            # Return the hospitals from the first
            # nearby district that has a suitable hospital.
            return current_district_results

        # Keep unsuitable hospitals in case NO district
        # eventually has a suitable hospital.
        stage_2_results.extend(
            current_district_results
        )

    # ---------------------------------------------------------
    # FALLBACK WHEN NO SUITABLE HOSPITAL EXISTS ANYWHERE
    #
    # Return evaluated hospitals so the application can
    # explain that no hospital fully satisfies the requirements.
    # ---------------------------------------------------------

    if stage_1_results:

        return stage_1_results + stage_2_results

    return stage_2_results