// ============================================================
//  MOCK IN-MEMORY DATABASE
// ============================================================

const { v4: uuidv4 } = require("uuid");

// ── Airports ─────────────────────────────────────────────────
const airports = [
  { code: "DEL", name: "Indira Gandhi International", city: "Delhi", country: "India" },
  { code: "BOM", name: "Chhatrapati Shivaji Maharaj International", city: "Mumbai", country: "India" },
  { code: "BLR", name: "Kempegowda International", city: "Bengaluru", country: "India" },
  { code: "HYD", name: "Rajiv Gandhi International", city: "Hyderabad", country: "India" },
  { code: "MAA", name: "Chennai International", city: "Chennai", country: "India" },
  { code: "CCU", name: "Netaji Subhash Chandra Bose International", city: "Kolkata", country: "India" },
  { code: "DXB", name: "Dubai International", city: "Dubai", country: "UAE" },
  { code: "LHR", name: "Heathrow Airport", city: "London", country: "UK" },
  { code: "JFK", name: "John F. Kennedy International", city: "New York", country: "USA" },
  { code: "SIN", name: "Changi Airport", city: "Singapore", country: "Singapore" },
];

// ── Flights ───────────────────────────────────────────────────
let flights = [
  // 🔵 TODAY'S FLIGHTS (2026-04-07)
  {
    id: "FL009",
    flightNumber: "AI-101",
    airline: "Air India",
    origin: "DEL",
    destination: "BOM",
    departureTime: "2026-04-07T05:30:00",
    arrivalTime: "2026-04-07T07:45:00",
    totalSeats: 180,
    availableSeats: 25,
    priceEconomy: 5000,
    priceBusiness: 15000,
    status: "scheduled"
  },
  {
    id: "FL010",
    flightNumber: "6E-222",
    airline: "IndiGo",
    origin: "BOM",
    destination: "DEL",
    departureTime: "2026-04-07T08:00:00",
    arrivalTime: "2026-04-07T10:10:00",
    totalSeats: 200,
    availableSeats: 80,
    priceEconomy: 4200,
    priceBusiness: null,
    status: "scheduled"
  },
  {
    id: "FL011",
    flightNumber: "UK-808",
    airline: "Vistara",
    origin: "BLR",
    destination: "DEL",
    departureTime: "2026-04-07T11:00:00",
    arrivalTime: "2026-04-07T13:45:00",
    totalSeats: 220,
    availableSeats: 60,
    priceEconomy: 5500,
    priceBusiness: 16000,
    status: "scheduled"
  },
  {
    id: "FL012",
    flightNumber: "AI-407",
    airline: "Air India",
    origin: "DEL",
    destination: "HYD",
    departureTime: "2026-04-07T14:20:00",
    arrivalTime: "2026-04-07T16:30:00",
    totalSeats: 180,
    availableSeats: 0,
    priceEconomy: 4800,
    priceBusiness: 14000,
    status: "full"
  },
  {
    id: "FL013",
    flightNumber: "EK-505",
    airline: "Emirates",
    origin: "DXB",
    destination: "DEL",
    departureTime: "2026-04-07T21:00:00",
    arrivalTime: "2026-04-08T02:00:00",
    totalSeats: 350,
    availableSeats: 140,
    priceEconomy: 22000,
    priceBusiness: 70000,
    status: "scheduled"
  },

  // 🟢 EXISTING FLIGHTS
  { id: "FL001", flightNumber: "AI-202", airline: "Air India", origin: "DEL", destination: "BOM", departureTime: "2026-04-10T06:00:00", arrivalTime: "2026-04-10T08:10:00", totalSeats: 180, availableSeats: 45, priceEconomy: 4500, priceBusiness: 14000, status: "scheduled" },
  { id: "FL002", flightNumber: "6E-301", airline: "IndiGo", origin: "BOM", destination: "BLR", departureTime: "2026-04-10T09:30:00", arrivalTime: "2026-04-10T11:00:00", totalSeats: 200, availableSeats: 120, priceEconomy: 3200, priceBusiness: null, status: "scheduled" },
  { id: "FL003", flightNumber: "UK-955", airline: "Vistara", origin: "DEL", destination: "DXB", departureTime: "2026-04-11T02:15:00", arrivalTime: "2026-04-11T04:30:00", totalSeats: 250, availableSeats: 60, priceEconomy: 18000, priceBusiness: 55000, status: "scheduled" },
  { id: "FL004", flightNumber: "EK-501", airline: "Emirates", origin: "DXB", destination: "LHR", departureTime: "2026-04-11T08:00:00", arrivalTime: "2026-04-11T12:30:00", totalSeats: 400, availableSeats: 200, priceEconomy: 35000, priceBusiness: 90000, status: "scheduled" },
  { id: "FL005", flightNumber: "SQ-421", airline: "Singapore Air", origin: "SIN", destination: "JFK", departureTime: "2026-04-12T23:55:00", arrivalTime: "2026-04-13T06:00:00", totalSeats: 300, availableSeats: 10, priceEconomy: 60000, priceBusiness: 150000, status: "scheduled" },
  { id: "FL006", flightNumber: "AI-131", airline: "Air India", origin: "DEL", destination: "JFK", departureTime: "2026-04-13T01:00:00", arrivalTime: "2026-04-13T09:30:00", totalSeats: 300, availableSeats: 0, priceEconomy: 55000, priceBusiness: 130000, status: "full" },
  { id: "FL007", flightNumber: "6E-780", airline: "IndiGo", origin: "CCU", destination: "DEL", departureTime: "2026-04-10T07:45:00", arrivalTime: "2026-04-10T10:00:00", totalSeats: 180, availableSeats: 90, priceEconomy: 4000, priceBusiness: null, status: "scheduled" },
  { id: "FL008", flightNumber: "BA-117", airline: "British Airways", origin: "LHR", destination: "JFK", departureTime: "2026-04-14T10:00:00", arrivalTime: "2026-04-14T13:00:00", totalSeats: 350, availableSeats: 150, priceEconomy: 45000, priceBusiness: 110000, status: "scheduled" },
];
// ── Passengers ────────────────────────────────────────────────
let passengers = [
  { id: "P001", name: "Aryan Sharma",   email: "aryan@example.com",  phone: "+91-9876543210", passportNumber: "Z1234567" },
  { id: "P002", name: "Priya Mehta",    email: "priya@example.com",  phone: "+91-9988776655", passportNumber: "Z7654321" },
  { id: "P003", name: "Rohan Verma",    email: "rohan@example.com",  phone: "+91-9001122334", passportNumber: "A1122334" },
];

// ── Bookings ──────────────────────────────────────────────────
let bookings = [
  { id: "BK001", flightId: "FL001", passengerId: "P001", seatClass: "economy",  seatNumber: "12A", totalFare: 4500,  bookingDate: "2026-03-20", status: "confirmed", paymentStatus: "paid" },
  { id: "BK002", flightId: "FL003", passengerId: "P002", seatClass: "business", seatNumber: "3C", totalFare: 55000, bookingDate: "2026-03-22", status: "confirmed", paymentStatus: "paid" },
];

// ── Helpers ───────────────────────────────────────────────────
const generateSeatNumber = (cls) => {
  const row = Math.floor(Math.random() * 30) + 1;
  const col = ["A","B","C","D","E","F"][Math.floor(Math.random() * 6)];
  return `${cls === "business" ? row : row + 10}${col}`;
};

module.exports = { airports, flights, passengers, bookings, generateSeatNumber, uuidv4 };
