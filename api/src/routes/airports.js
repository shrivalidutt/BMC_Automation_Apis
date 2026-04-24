// ============================================================
//  AIRPORT ROUTES
// ============================================================
const express = require("express");
const router = express.Router();
const { airports, flights } = require("../data/db");

/**
 * GET /api/airports
 * List all airports.
 * Query params (optional): country, city
 */
router.get("/", (req, res) => {
  const { country, city } = req.query;
  let results = [...airports];
  if (country) results = results.filter(a => a.country.toLowerCase() === country.toLowerCase());
  if (city)    results = results.filter(a => a.city.toLowerCase().includes(city.toLowerCase()));
  res.json({ success: true, count: results.length, data: results });
});

/**
 * GET /api/airports/:code
 * Get airport details + its outgoing flights.
 * Query param (optional): date – filter outgoing flights by date
 */
router.get("/:code", (req, res) => {
  const airport = airports.find(a => a.code.toUpperCase() === req.params.code.toUpperCase());
  if (!airport) return res.status(404).json({ success: false, error: "Airport not found" });

  let outgoing = flights.filter(f => f.origin === airport.code);
  if (req.query.date) outgoing = outgoing.filter(f => f.departureTime.startsWith(req.query.date));

  res.json({ success: true, data: { ...airport, outgoingFlights: outgoing } });
});

module.exports = router;
