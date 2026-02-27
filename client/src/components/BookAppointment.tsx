import React from "react";
import { useParams } from "react-router-dom";

const BookAppointment: React.FC = () => {
  const { doctorId } = useParams<{ doctorId: string }>();

  return (
    <div className="page-content">
      <h1 className="booking-title">Booked Appointment</h1>
      <div className="booking-card">
        <p>You are initiating a booking for Doctor ID: <strong>{doctorId}</strong></p>
        <p>Please select a time slot to continue.</p>
      </div>
    </div>
  );
};

export default BookAppointment;