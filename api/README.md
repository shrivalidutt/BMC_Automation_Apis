# ✈️ Flight Booking Simulator API

A Node.js + Express REST API simulator for a flight booking system, backed by a mock in-memory database. No external database required.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Start the server
npm start

# 3. Open in browser or test with curl
# http://localhost:3000/api
```

---

## 📁 Project Structure

```
flight-booking-simulator/
├── index.js                   ← Entry point
├── package.json
├── README.md
└── src/
    ├── data/
    │   └── db.js              ← Mock in-memory database
    ├── middleware/
    │   └── index.js           ← Logger, error handler, field validator
    └── routes/
        ├── airports.js        ← Airport APIs
        ├── flights.js         ← Flight APIs
        ├── passengers.js      ← Passenger APIs
        └── bookings.js        ← Booking APIs
```

---

## 🗺️ API Reference

### Root
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api` | API index — lists all endpoints |

---

### ✈️ Airports

| Method | Endpoint | Required Params | Optional Params |
|--------|----------|-----------------|-----------------|
| GET | `/api/airports` | – | `country`, `city` |
| GET | `/api/airports/:code` | `code` (path) | `date` (query) |

```bash
# All airports
curl http://localhost:3000/api/airports

# Filter by country
curl "http://localhost:3000/api/airports?country=India"

# Airport detail with outgoing flights on a date
curl "http://localhost:3000/api/airports/DEL?date=2026-04-10"
```

---

### 🛫 Flights

| Method | Endpoint | Required Params | Optional Params |
|--------|----------|-----------------|-----------------|
| GET | `/api/flights` | – | `origin`, `destination`, `date`, `airline`, `seatClass`, `maxPrice`, `onlyAvailable` |
| GET | `/api/flights/:id` | `id` (path) | – |
| GET | `/api/flights/:id/availability` | `id` (path) | `seatClass` |
| PATCH | `/api/flights/:id/status` | `id` (path), `status` (body) | – |

```bash
# All available flights
curl http://localhost:3000/api/flights

# Search DEL → BOM on a date
curl "http://localhost:3000/api/flights?origin=DEL&destination=BOM&date=2026-04-10"

# Cheap economy tickets under ₹5000
curl "http://localhost:3000/api/flights?seatClass=economy&maxPrice=5000"

# Single flight
curl http://localhost:3000/api/flights/FL001

# Seat availability
curl http://localhost:3000/api/flights/FL003/availability?seatClass=business

# Update flight status (admin)
curl -X PATCH http://localhost:3000/api/flights/FL002/status \
  -H "Content-Type: application/json" \
  -d '{"status": "delayed"}'
```

---

### 👤 Passengers

| Method | Endpoint | Required Body | Optional |
|--------|----------|---------------|----------|
| GET | `/api/passengers` | – | `name`, `email` (query) |
| GET | `/api/passengers/:id` | `id` (path) | – |
| POST | `/api/passengers` | `name`, `email`, `phone` | `passportNumber` |
| PUT | `/api/passengers/:id` | `id` (path) | `name`, `phone`, `passportNumber` |
| DELETE | `/api/passengers/:id` | `id` (path) | – |

```bash
# List all passengers
curl http://localhost:3000/api/passengers

# Search by name
curl "http://localhost:3000/api/passengers?name=Priya"

# Register new passenger
curl -X POST http://localhost:3000/api/passengers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kavya Nair",
    "email": "kavya@example.com",
    "phone": "+91-9123456789",
    "passportNumber": "B9988776"
  }'

# Update passenger
curl -X PUT http://localhost:3000/api/passengers/P001 \
  -H "Content-Type: application/json" \
  -d '{"phone": "+91-9000000001"}'

# Delete passenger
curl -X DELETE http://localhost:3000/api/passengers/P003
```

---

### 🎫 Bookings

| Method | Endpoint | Required | Optional |
|--------|----------|----------|----------|
| GET | `/api/bookings` | – | `passengerId`, `flightId`, `status` (query) |
| GET | `/api/bookings/:id` | `id` (path) | – |
| POST | `/api/bookings` | `flightId`, `passengerId`, `seatClass` | `specialMeal`, `extraBaggage` |
| PATCH | `/api/bookings/:id/cancel` | `id` (path) | `reason` (body) |

```bash
# All bookings
curl http://localhost:3000/api/bookings

# Filter bookings by passenger
curl "http://localhost:3000/api/bookings?passengerId=P001"

# Full booking detail
curl http://localhost:3000/api/bookings/BK001

# Create a booking
curl -X POST http://localhost:3000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "flightId": "FL002",
    "passengerId": "P003",
    "seatClass": "economy",
    "specialMeal": "vegetarian",
    "extraBaggage": true
  }'

# Cancel a booking
curl -X PATCH http://localhost:3000/api/bookings/BK001/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "Change of plans"}'
```

---

## 🗄️ Mock Database

### Pre-loaded Data
- **10 Airports** — DEL, BOM, BLR, HYD, MAA, CCU, DXB, LHR, JFK, SIN
- **8 Flights** — covering domestic & international routes with varied airlines & prices
- **3 Passengers** — sample passengers ready to use
- **2 Bookings** — pre-existing bookings for demo

### Business Logic
- Booking a seat decrements `availableSeats` on the flight
- When `availableSeats` reaches 0, flight status becomes `"full"`
- Cancelling a booking restores the seat count
- Duplicate bookings (same passenger + flight) are rejected
- Business class not offered on low-cost carriers (e.g. IndiGo)

---

## 🧪 Full Booking Flow (step-by-step)

```bash
# Step 1 – Search for a flight
curl "http://localhost:3000/api/flights?origin=DEL&destination=BOM&date=2026-04-10"

# Step 2 – Register a new passenger
curl -X POST http://localhost:3000/api/passengers \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","phone":"+91-9000000000"}'

# Step 3 – Book a seat (use IDs from steps 1 & 2)
curl -X POST http://localhost:3000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"flightId":"FL001","passengerId":"P004","seatClass":"economy"}'

# Step 4 – View booking confirmation
curl http://localhost:3000/api/bookings/BK003

# Step 5 – Cancel if needed
curl -X PATCH http://localhost:3000/api/bookings/BK003/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason":"Refund requested"}'
```
