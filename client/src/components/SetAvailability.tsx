import { useState } from "react";
import toast from "react-hot-toast";
import { postData } from "../helper/apiCall";

import "../styles/setAvailability.css"

const daysList = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export const SetAvailability = () => {
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSet, setIsSet] = useState(false);

  const toggleDay = (day: string) => {
    if (selectedDays.includes(day)) {
      setSelectedDays(selectedDays.filter((d) => d !== day));
    } else {
      setSelectedDays([...selectedDays, day]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedDays.length === 0) {
      toast.error("Select at least one day");
      return;
    }

    setIsSubmitting(true);

    try {
      await postData("/doctors/availability", {
        days_of_week: selectedDays,
        start_time: startTime,
        end_time: endTime,
      });

      toast.success("Availability set successfully");
      setIsSubmitting(false);
      setIsSet(true);
      // keep form values so "Update Availability" reopens with current values
    } catch (err: any) {
      setIsSubmitting(false);
      toast.error(err?.response?.data?.detail || "Failed to set availability");
    }
  };

  return (
    <div className="availability-container">
      <h2>Set Availability</h2>

      {isSubmitting ? (
        <div className="status-message">Setting availability</div>
      ) : isSet ? (
        <div className="status-after">
          <div className="status-message">Availability is set</div>
          <button
            type="button"
            className="update-btn"
            onClick={() => setIsSet(false)}
          >
            Update Availability
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="availability-form">
          <div className="days-container">
            {daysList.map((day) => (
              <label key={day} className="day-checkbox">
                <input
                  type="checkbox"
                  checked={selectedDays.includes(day)}
                  onChange={() => toggleDay(day)}
                />
                {day}
              </label>
            ))}
          </div>

          <div className="time-inputs">
            <div>
              <label>Start Time</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
              />
            </div>

            <div>
              <label>End Time</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="submit-btn">
            Save Availability
          </button>
        </form>
      )}
    </div>
  );
};
