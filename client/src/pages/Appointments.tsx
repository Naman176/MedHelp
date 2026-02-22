import React, { useEffect, useState } from 'react';
import fetchData from "../helper/apiCall";
import toast from "react-hot-toast";
import "../styles/appointments.css"

interface Appointment {
  id: string;
  doctor_id: string;
  patient_id: string;
  appointment_date: string;
  appointment_time: string;
  status: string;
  appointment_type: string;
  meeting_link?: string;
}

const Appointments: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  const getAppointments = async () => {
    try {
      const data = await fetchData("/appointments/");
      setAppointments(data);
    } catch (error) {
      toast.error("Failed to load appointments");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getAppointments();
  }, []);

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'scheduled': return 'status-pending';
      case 'completed': return 'status-success';
      case 'cancelled': return 'status-error';
      default: return '';
    }
  };

  if (loading) return <div className="loader">Loading your schedule...</div>;

  return (
    <div className="appointments-container">
      <div className="table-header">
        <h2>Your Appointments</h2>
        <button className="btn-primary" onClick={getAppointments}>Refresh</button>
      </div>

      <div className="table-wrapper">
        <table className="med-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Type</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {appointments.length > 0 ? (
              appointments.map((apt) => (
                <tr key={apt.id}>
                  <td>{new Date(apt.appointment_date).toLocaleDateString()}</td>
                  <td>{apt.appointment_time}</td>
                  <td><span className="type-tag">{apt.appointment_type.split('_').join(' ')}</span></td>
                  <td>
                    <span className={`status-badge ${getStatusClass(apt.status)}`}>
                      {apt.status}
                    </span>
                  </td>
                  <td>
                    {apt.meeting_link && apt.appointment_type === "VIRTUAL" ? (
                      <a href={apt.meeting_link} target="_blank" rel="noreferrer" className="join-link">
                        Join Meeting
                      </a>
                    ) : (
                      <span className="text-muted">In-Person</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="no-data">No appointments found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Appointments;