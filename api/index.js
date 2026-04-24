// ============================================================
//  FLIGHT BOOKING SIMULATOR — Entry Point
//  Run: node index.js
//  Then open: http://localhost:3000/api
// ============================================================

const express = require("express");
const app = express();

// ── Middleware ────────────────────────────────────────────────
const { requestLogger, notFound, errorHandler } = require("./src/middleware");
app.use(express.json());
app.use(requestLogger);

// ── Routes ────────────────────────────────────────────────────
const flightRoutes    = require("./src/routes/flights");
const passengerRoutes = require("./src/routes/passengers");
const bookingRoutes   = require("./src/routes/bookings");
const airportRoutes   = require("./src/routes/airports");

app.use("/api/flights",    flightRoutes);
app.use("/api/passengers", passengerRoutes);
app.use("/api/bookings",   bookingRoutes);
app.use("/api/airports",   airportRoutes);

// ── API Index ─────────────────────────────────────────────────
app.get("/api", (req, res) => {
  res.json({
    message: "✈️  Flight Booking Simulator API",
    version: "1.0.0",
    endpoints: {
      airports: {
        "GET  /api/airports":                  "List airports (optional: ?country=India&city=Delhi)",
        "GET  /api/airports/:code":            "Get airport + outgoing flights (optional: ?date=2026-04-10)",
      },
      flights: {
        "GET  /api/flights":                   "Search flights (optional: ?origin=DEL&destination=BOM&date=2026-04-10&airline=IndiGo&seatClass=economy&maxPrice=5000&onlyAvailable=true)",
        "GET  /api/flights/:id":               "Get flight by ID",
        "GET  /api/flights/:id/availability":  "Check seat availability (optional: ?seatClass=business)",
        "PATCH /api/flights/:id/status":       "Update flight status — body: { status }",
      },
      passengers: {
        "GET  /api/passengers":                "List passengers (optional: ?name=Aryan&email=...)",
        "GET  /api/passengers/:id":            "Get passenger by ID",
        "POST /api/passengers":                "Register passenger — body: { name, email, phone, passportNumber? }",
        "PUT  /api/passengers/:id":            "Update passenger — body: { name?, phone?, passportNumber? }",
        "DELETE /api/passengers/:id":          "Delete passenger",
      },
      bookings: {
        "GET  /api/bookings":                  "List bookings (optional: ?passengerId=P001&flightId=FL001&status=confirmed)",
        "GET  /api/bookings/:id":              "Get booking with enriched details",
        "POST /api/bookings":                  "Create booking — body: { flightId, passengerId, seatClass, specialMeal?, extraBaggage? }",
        "PATCH /api/bookings/:id/cancel":      "Cancel booking — body: { reason? }",
      },
    },
  });
});

// ── Error Handling ─────────────────────────────────────────────
app.use(notFound);
app.use(errorHandler);

// ── Start ──────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n✈️  Flight Booking Simulator running on http://localhost:${PORT}/api\n`);
  console.log("Press Ctrl+C to stop.\n");
});
