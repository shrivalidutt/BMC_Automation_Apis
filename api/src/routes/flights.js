// ============================================================
//  FLIGHT ROUTES
// ============================================================
const express = require("express");
const router = express.Router();
const { flights } = require("../data/db");

/**
 * GET /api/flights
 * Search flights with optional filters.
 *
 * Query params (all optional):
 *   origin        – IATA code  e.g. DEL
 *   destination   – IATA code  e.g. BOM
 *   date          – YYYY-MM-DD departure date filter
 *   airline       – partial airline name match
 *   seatClass     – "economy" | "business"
 *   maxPrice      – number, max price for chosen class
 *   onlyAvailable – "true" to hide full flights (default true)
 */
router.get("/", (req, res) => {
  let { origin, destination, date, airline, seatClass, maxPrice, onlyAvailable = "true" } = req.query;

  let results = [...flights];

  if (origin)      results = results.filter(f => f.origin.toUpperCase() === origin.toUpperCase());
  if (destination) results = results.filter(f => f.destination.toUpperCase() === destination.toUpperCase());
  if (date)        results = results.filter(f => f.departureTime.startsWith(date));
  if (airline)     results = results.filter(f => f.airline.toLowerCase().includes(airline.toLowerCase()));
  if (onlyAvailable === "true") results = results.filter(f => f.availableSeats > 0);

  if (seatClass && maxPrice) {
    const priceKey = seatClass === "business" ? "priceBusiness" : "priceEconomy";
    results = results.filter(f => f[priceKey] !== null && f[priceKey] <= Number(maxPrice));
  }

  res.json({ success: true, count: results.length, data: results });
});

/**
 * GET /api/flights/:id
 * Get a single flight by its ID.
 * Path param: id (required)
 */
router.get("/:id", (req, res) => {
  const flight = flights.find(f => f.id === req.params.id);
  if (!flight) return res.status(404).json({ success: false, error: "Flight not found" });
  res.json({ success: true, data: flight });
});

/**
 * GET /api/flights/:id/availability
 * Check seat availability broken down by class.
 * Query param: seatClass (optional) – "economy" | "business"
 */
router.get("/:id/availability", (req, res) => {
  const flight = flights.find(f => f.id === req.params.id);
  if (!flight) return res.status(404).json({ success: false, error: "Flight not found" });

  const { seatClass } = req.query;
  const response = {
    flightId: flight.id,
    flightNumber: flight.flightNumber,
    status: flight.status,
    totalSeats: flight.totalSeats,
    availableSeats: flight.availableSeats,
    economy: { price: flight.priceEconomy, available: flight.availableSeats > 0 },
    business: flight.priceBusiness
      ? { price: flight.priceBusiness, available: flight.availableSeats > 0 }
      : null,
  };

  if (seatClass) {
    const key = seatClass === "business" ? "business" : "economy";
    return res.json({ success: true, data: { seatClass: key, ...response[key], flightId: flight.id } });
  }

  res.json({ success: true, data: response });
});

/**
 * PATCH /api/flights/:id/status
 * Update a flight's status (admin use).
 * Body: { status: "scheduled"|"delayed"|"cancelled"|"full" }
 */
router.patch("/:id/status", (req, res) => {
  const { status } = req.body;
  const allowed = ["scheduled", "delayed", "cancelled", "full"];
  if (!status || !allowed.includes(status)) {
    return res.status(400).json({ success: false, error: `status must be one of: ${allowed.join(", ")}` });
  }

  const flight = flights.find(f => f.id === req.params.id);
  if (!flight) return res.status(404).json({ success: false, error: "Flight not found" });

  flight.status = status;
  res.json({ success: true, message: "Flight status updated", data: flight });
});

module.exports = router;
