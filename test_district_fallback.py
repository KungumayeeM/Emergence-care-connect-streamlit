from ai import hospital_matching
from Backend.database import get_all_hospitals


print("=" * 70)
print("DISTRICT FALLBACK TEST")
print("=" * 70)

# ---------------------------------------------------------
# Create temporary Tiruvallur hospital for testing
# ---------------------------------------------------------

real_hospitals = get_all_hospitals(verified_only=True)

temporary_hospital = dict(real_hospitals[0])

temporary_hospital["hospital_id"] = "TEST-TIRUVALLUR"
temporary_hospital["hospital_name"] = "Temporary Tiruvallur Hospital"

# Fixed test coordinates for Tiruvallur
temporary_hospital["latitude"] = 13.1439
temporary_hospital["longitude"] = 79.9082

# Make ICU unavailable so Stage 1 cannot satisfy the patient
temporary_hospital["icu_available"] = 0

# Keep emergency bed available
temporary_hospital["emergency_beds"] = 10


# ---------------------------------------------------------
# Temporarily replace database hospital list
# ---------------------------------------------------------

original_function = hospital_matching.get_all_hospitals


def test_hospitals(verified_only=False):
    return [temporary_hospital] + real_hospitals


hospital_matching.get_all_hospitals = test_hospitals


# ---------------------------------------------------------
# Patient located in Tiruvallur
# ---------------------------------------------------------

patient = {
    "name": "Tiruvallur Fallback Test",
    "age": 30,
    "emergency_type": "Accident",
    "consciousness": "Conscious",
    "breathing": "Normal",
    "bleeding": "No",
    "severity": "Severe",
    "required_resources": ["icu"],
    "specialist": ""
}

location = {
    "latitude": 13.1439,
    "longitude": 79.9082
}


# ---------------------------------------------------------
# Run hospital matching
# ---------------------------------------------------------

results = hospital_matching.match_hospitals(
    patient,
    location
)


print()
print("Patient District: Tiruvallur")
print("Required Resource: ICU")
print()
print("-" * 70)


for i, hospital in enumerate(results):
    print(
        i + 1,
        "|",
        hospital["hospital_name"],
        "| District:",
        hospital["district"],
        "| Match:",
        hospital["district_match"],
        "| Eligible:",
        hospital["eligible"],
        "| Score:",
        hospital["suitability_score"]
    )


# ---------------------------------------------------------
# Verify fallback behavior
# ---------------------------------------------------------

print()
print("-" * 70)
print("FALLBACK VERIFICATION")
print("-" * 70)

# The temporary Tiruvallur hospital should NOT be eligible
# because ICU is unavailable.
assert temporary_hospital["icu_available"] == 0

# The result should come from a nearby district.
assert len(results) > 0

# All returned hospitals should be from the fallback district.
assert all(
    hospital["district"] != "Tiruvallur"
    for hospital in results
)

# At least one nearby hospital should be eligible.
assert any(
    hospital["eligible"]
    for hospital in results
)

# Returned hospitals should explicitly show nearby district.
assert all(
    "Nearby district:" in hospital["district_match"]
    for hospital in results
)


# ---------------------------------------------------------
# Display best hospital
# ---------------------------------------------------------

best_hospital = results[0]

print()
print("BEST FALLBACK HOSPITAL")
print("-" * 70)
print("Hospital:", best_hospital["hospital_name"])
print("District:", best_hospital["district"])
print("District Match:", best_hospital["district_match"])
print("Eligible:", best_hospital["eligible"])
print("Score:", best_hospital["suitability_score"])


# ---------------------------------------------------------
# Restore original function
# ---------------------------------------------------------

hospital_matching.get_all_hospitals = original_function


print()
print("=" * 70)
print("✅ DISTRICT FALLBACK TEST PASSED")
print("=" * 70)