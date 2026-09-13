# EmergencyCare Connect — Working MVP Prototype

AI-assisted emergency hospital matching, resource reservation, capacity management and ambulance coordination.

## What is implemented
- Patient emergency request
- GPS browser location (with permission)
- Hospital database in SQLite
- Hospital capacity APIs
- AI-assisted rule-based hospital ranking
- Clinical/resource suitability before distance
- Capacity freshness and ETA in ranking
- Time-bound reservation request
- Hospital confirmation
- Reservation consumes ICU/ventilator/emergency-bed capacity
- Transport → Arrived → Admitted workflow
- Reservation cancellation/expiry support
- Ambulance registration API
- Government/admin network summary API
- Simple browser dashboard

## Important prototype limitation
The hospital dataset is synthetic. Capacity is not real-time until a participating hospital system/API is connected. The matching engine is transparent rule-based assistance, not a clinically validated diagnostic or treatment model.

## Run
1. Open PowerShell in this project folder.
2. Activate your existing environment:
   `.venv\\Scripts\\Activate.ps1`
3. Install requirements if needed:
   `py -m pip install -r requirements.txt`
4. Start:
   `uvicorn Backend.main:app --reload`
5. Open:
   `http://127.0.0.1:8000/dashboard`
6. API documentation:
   `http://127.0.0.1:8000/docs`

Do not type Python functions such as `initialize_database()` directly into PowerShell.

## Demo flow
Road accident → GPS → select ICU/ventilator/trauma → Find Suitable Hospitals → choose eligible hospital → Reserve Resources → Hospital Confirms → Start Transport → Mark Arrived → Admit Patient.

## API highlights
GET `/hospitals`
GET `/hospitals/{id}/capacity`
PUT `/hospitals/{id}/capacity`
POST `/match-hospitals`
POST `/reserve`
POST `/reservations/{id}/confirm`
POST `/reservations/{id}/transport`
POST `/reservations/{id}/arrive`
POST `/reservations/{id}/admit`
POST `/reservations/{id}/cancel`
GET `/reservations`
POST `/reservations/{id}/fallback?latitude=...&longitude=...`
POST `/transfers`
POST `/ambulances`
GET `/ambulances`
GET `/dashboard/summary`

## Next production-oriented enhancements
- Secure hospital authentication and role-based access
- Real HIS/EHR/bed-management integration and validated interoperability
- Real ambulance tracking and ETA/traffic data
- Event-driven capacity synchronization
- Notifications and audit logs
- Hospital-to-hospital transfer workflow
- Dynamic fallback/re-reservation when destination capacity changes
- Validated ML/predictive models using appropriate healthcare data
- Security, privacy, consent and regulatory validation
