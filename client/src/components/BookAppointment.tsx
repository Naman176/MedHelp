import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import fetchData, { postData } from "../helper/apiCall";
import "../styles/bookAppointment.css";

interface Availability {
  days_of_week: string; // e.g., "Monday"
  start_time: string;   
  end_time: string;     
}

const BookAppointment: React.FC = () => {
  const { doctorId } = useParams<{ doctorId: string }>();

  // State Management
  const [schedule, setSchedule] = useState<Availability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const [bookedSlots, setBookedSlots] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    appointment_date: "",
    appointment_time: "",
    appointment_type: "CONSULTATION",
  });

useEffect(() => {
  const fetchSchedule = async () => {
    try {
      const data = await fetchData(`/doctors/${doctorId}/availability`);
      setSchedule(data);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Could not fetch doctor schedule"
      );
    } finally {
      setLoading(false);
    }
  };

  if (doctorId) fetchSchedule();
}, [doctorId]);

useEffect(() => {
  if (!doctorId || !formData.appointment_date) return;

  const fetchBookedSlots = async () => {
    try {
      const data = await fetchData(
        `/appointments/booked?doctor_id=${doctorId}&date=${formData.appointment_date}`
      );
      setBookedSlots(data); // ["10:00","10:30"]
    } catch {
      setBookedSlots([]);
    }
  };

  fetchBookedSlots();
}, [doctorId, formData.appointment_date]);

  // 2. Helper: Find the rule for a specific chosen date
  const getRuleForDate = (dateString: string) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    // Adjusting for timezone to get the correct day name
    const dayName = new Intl.DateTimeFormat('en-US', { weekday: 'long' }).format(date);
    return schedule.find(s => s.days_of_week === dayName);
  };

  const generateTimeSlots = (start: string, end: string) => {
  const slots: string[] = [];

  const [startH, startM] = start.split(":").map(Number);
  const [endH, endM] = end.split(":").map(Number);

  let current = startH * 60 + startM;
  const endTime = endH * 60 + endM;

  while (current + 30 <= endTime) {
    const h = Math.floor(current / 60).toString().padStart(2, "0");
    const m = (current % 60).toString().padStart(2, "0");
    slots.push(`${h}:${m}`);
    current += 30;
  }

  return slots;
};

  const selectedRule = getRuleForDate(formData.appointment_date);
  const timeSlots = selectedRule
  ? generateTimeSlots(selectedRule.start_time, selectedRule.end_time)
      .filter(slot => !bookedSlots.includes(slot))
  : [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
    setLoading(true);

    await postData("/appointments/book", {
      doctor_id: doctorId,
      appointment_date: formData.appointment_date,
      appointment_time: formData.appointment_time,
      appointment_type: 'VIRTUAL',
    });

    setSuccess(true);
    setTimeout(() => navigate("/appointments"), 2000);

  } catch (err: any) {
    const detail = err.response?.data?.detail;

    if (typeof detail === "string") {
      setError(detail); // "This time slot is already booked."
    } else if (Array.isArray(detail)) {
      setError(detail[0].msg);
    } else {
      setError("Failed to book appointment");
    }
  } finally {
    setLoading(false);
  }
  };

  if (loading) return <div>Loading...</div>;
  if (success) {
    return (
      <div className="page-content">
        <div className="alert-success">
          <h2>Booking Successful!</h2>
          <p>Redirecting to your appointments...</p>
        </div>
      </div>
    );
  }
  return (
    <div className="page-content">
      <h1 className="booking-title">Schedule Appointment</h1>
      
      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="booking-form">
        {/* DATE INPUT */}
        <div className="form-group">
          <label>Appointment Date</label>
          <input 
            type="date"
            required
            min={new Date().toISOString().split("T")[0]} // Prevents past dates
            onChange={(e) => {
              const rule = getRuleForDate(e.target.value);
              if (!rule) {
                alert("Doctor does not work on this day. Please pick another.");
                setFormData({ ...formData, appointment_date: "" });
              } else {
                setFormData({ ...formData, appointment_date: e.target.value });
              }
            }}
          />
        </div>

        <div className="form-group">
          <label>Appointment Time</label>

          <select
            required
            disabled={!selectedRule}
            value={formData.appointment_time}
            onChange={(e) =>
              setFormData({ ...formData, appointment_time: e.target.value })
            }
          >
            <option value="">Select a time</option>

            {timeSlots.map((slot) => (
              <option key={slot} value={slot}>
                {slot}
              </option>
            ))}
          </select>

          {selectedRule && (
            <p className="hint">
              Doctor is available: {selectedRule.start_time} - {selectedRule.end_time}
            </p>
          )}
        </div>

        <button type="submit" className="btn-book" disabled={!formData.appointment_time}>
          Request Booking
        </button>
      </form>
    </div>
  );
};

export default BookAppointment;