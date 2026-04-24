// ============================================================
//  BOOKING ROUTES
// ============================================================
const express = require("express");
const router = express.Router();
const { bookings, flights, passengers, generateSeatNumber, uuidv4 } = require("../data/db");
const { requireFields } = require("../middleware");

/**
 * GET /api/bookings
 * List bookings.
 * Query params (all optional):
 *   passengerId – filter by passenger
 *   flightId    – filter by flight
 *   status      – "confirmed" | "cancelled" | "pending"
 */
router.get("/", (req, res) => {
  const { passengerId, flightId, status } = req.query;
  let results = [...bookings];
  if (passengerId) results = results.filter(b => b.passengerId === passengerId);
  if (flightId)    results = results.filter(b => b.flightId === flightId);
  if (status)      results = results.filter(b => b.status === status);
  res.json({ success: true, count: results.length, data: results });
});

/**
 * GET /api/bookings/:id
 * Get full booking details with enriched flight & passenger info.
 */
router.get("/:id", (req, res) => {
  const booking = bookings.find(b => b.id === req.params.id);
  if (!booking) return res.status(404).json({ success: false, error: "Booking not found" });

  const flight    = flights.find(f => f.id === booking.flightId);
  const passenger = passengers.find(p => p.id === booking.passengerId);

  res.json({
    success: true,
    data: {
      ...booking,
      flightDetails: flight || null,
      passengerDetails: passenger || null,
    },
  });
});

/**
 * POST /api/bookings
 * Create a new booking.
 * Body (required): flightId, passengerId, seatClass
 * Body (optional): specialMeal, extraBaggage (boolean)
 */
router.post(
  "/",
  requireFields("flightId", "passengerId", "seatClass"),
  (req, res) => {
    const { flightId, passengerId, seatClass, specialMeal, extraBaggage } = req.body;

    const flight    = flights.find(f => f.id === flightId);
    const passenger = passengers.find(p => p.id === passengerId);

    if (!flight)    return res.status(404).json({ success: false, error: "Flight not found" });
    if (!passenger) return res.status(404).json({ success: false, error: "Passenger not found" });
    if (flight.availableSeats === 0) return res.status(409).json({ success: false, error: "No seats available on this flight" });
    if (!["economy", "business"].includes(seatClass)) {
      return res.status(400).json({ success: false, error: "seatClass must be 'economy' or 'business'" });
    }
    if (seatClass === "business" && !flight.priceBusiness) {
      return res.status(400).json({ success: false, error: "This flight does not offer business class" });
    }

    // Check duplicate booking
    if (bookings.find(b => b.flightId === flightId && b.passengerId === passengerId && b.status !== "cancelled")) {
      return res.status(409).json({ success: false, error: "Passenger already has an active booking for this flight" });
    }

    const basePrice  = seatClass === "business" ? flight.priceBusiness : flight.priceEconomy;
    const baggageFee = extraBaggage ? 1500 : 0;
    const totalFare  = basePrice + baggageFee;

    const newBooking = {
      id: "BK" + String(bookings.length + 1).padStart(3, "0"),
      flightId,
      passengerId,
      seatClass,
      seatNumber: generateSeatNumber(seatClass),
      totalFare,
      specialMeal: specialMeal || null,
      extraBaggage: !!extraBaggage,
      bookingDate: new Date().toISOString().split("T")[0],
      status: "confirmed",
      paymentStatus: "paid",
    };

    bookings.push(newBooking);
    flight.availableSeats -= 1;
    if (flight.availableSeats === 0) flight.status = "full";

    res.status(201).json({ success: true, message: "Booking confirmed!", data: newBooking });
  }
);

/**
 * PATCH /api/bookings/:id/cancel
 * Cancel a booking.
 * Body (optional): reason
 */
router.patch("/:id/cancel", (req, res) => {
  const booking = bookings.find(b => b.id === req.params.id);
  if (!booking) return res.status(404).json({ success: false, error: "Booking not found" });
  if (booking.status === "cancelled") {
    return res.status(409).json({ success: false, error: "Booking is already cancelled" });
  }

  booking.status = "cancelled";
  booking.cancellationReason = req.body.reason || "Not specified";
  booking.cancelledAt = new Date().toISOString();

  // Restore seat
  const flight = flights.find(f => f.id === booking.flightId);
  if (flight) {
    flight.availableSeats += 1;
    if (flight.status === "full") flight.status = "scheduled";
  }

  res.json({ success: true, message: "Booking cancelled", data: booking });
});

module.exports = router;
