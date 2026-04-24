// ============================================================
//  PASSENGER ROUTES
// ============================================================
const express = require("express");
const router = express.Router();
const { passengers, uuidv4 } = require("../data/db");
const { requireFields } = require("../middleware");

/**
 * GET /api/passengers
 * List all passengers.
 * Query params (all optional):
 *   name  – partial name search
 *   email – exact email match
 */
router.get("/", (req, res) => {
  const { name, email } = req.query;
  let results = [...passengers];
  if (name)  results = results.filter(p => p.name.toLowerCase().includes(name.toLowerCase()));
  if (email) results = results.filter(p => p.email === email);
  res.json({ success: true, count: results.length, data: results });
});

/**
 * GET /api/passengers/:id
 * Get a single passenger by ID.
 */
router.get("/:id", (req, res) => {
  const p = passengers.find(p => p.id === req.params.id);
  if (!p) return res.status(404).json({ success: false, error: "Passenger not found" });
  res.json({ success: true, data: p });
});

/**
 * POST /api/passengers
 * Register a new passenger.
 * Body (required): name, email, phone
 * Body (optional): passportNumber
 */
router.post("/", requireFields("name", "email", "phone"), (req, res) => {
  const { name, email, phone, passportNumber } = req.body;

  if (passengers.find(p => p.email === email)) {
    return res.status(409).json({ success: false, error: "A passenger with this email already exists" });
  }

  const newPassenger = {
    id: "P" + String(passengers.length + 1).padStart(3, "0"),
    name,
    email,
    phone,
    passportNumber: passportNumber || null,
  };

  passengers.push(newPassenger);
  res.status(201).json({ success: true, message: "Passenger registered successfully", data: newPassenger });
});

/**
 * PUT /api/passengers/:id
 * Update passenger details.
 * Body (all optional): name, phone, passportNumber
 */
router.put("/:id", (req, res) => {
  const p = passengers.find(p => p.id === req.params.id);
  if (!p) return res.status(404).json({ success: false, error: "Passenger not found" });

  const { name, phone, passportNumber } = req.body;
  if (name)           p.name = name;
  if (phone)          p.phone = phone;
  if (passportNumber) p.passportNumber = passportNumber;

  res.json({ success: true, message: "Passenger updated", data: p });
});

/**
 * DELETE /api/passengers/:id
 * Remove a passenger record.
 */
router.delete("/:id", (req, res) => {
  const idx = passengers.findIndex(p => p.id === req.params.id);
  if (idx === -1) return res.status(404).json({ success: false, error: "Passenger not found" });

  const [removed] = passengers.splice(idx, 1);
  res.json({ success: true, message: "Passenger deleted", data: removed });
});

module.exports = router;
