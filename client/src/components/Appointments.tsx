import React, { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import fetchData from "../helper/apiCall";
import toast from "react-hot-toast";
import { setAppointments } from "../redux/reducers/rootSlice";
import { getAppointments } from "../redux/selectors/rootSelectors";
import "../styles/appointments.css";
import type { Appointment } from "../types";

const Appointments: React.FC = () => {
  const dispatch = useDispatch();
  
  // Get appointments from Redux store
  const appointments = useSelector(getAppointments);
  const [loading, setLoading] = useState(true);

  const fetchAppointments = async () => {
    try {
      const data = await fetchData("/appointments/");
      // Store in Redux instead of local state
      dispatch(setAppointments(data));
    } catch (error) {
      toast.error("Failed to load appointments");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if we don't have appointments yet (optional optimization)
    if (appointments.length === 0) {
      fetchAppointments();
    } else {
      setLoading(false);
    }
  }, []);

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "scheduled": return "status-pending";
      case "completed": return "status-success";
      case "cancelled": return "status-error";
      default: return "";
    }
  };

  if (loading) return <div className="loader">Loading your schedule...</div>;
  const renderMeetingCell = (apt: Appointment) => {
    if (apt.appointment_type === "VIRTUAL" && apt.meeting_link) {
      return (
        <a href={apt.meeting_link} target="_blank" rel="noreferrer" className="join-link">
          Join Meeting
        </a>
      );
    } else if (apt.appointment_type === "VIRTUAL" && apt.status === "PENDING") {
      return <span>Wait for confirmation</span>;
    } else if (apt.appointment_type === "IN_PERSON") {
      return <span className="text-muted">In-Person</span>;
    }
    else {
      return <span className="text-muted">N/A</span>;
    }
  };
  return (
    <div className="appointments-container">
      <div className="table-header">
        <h2>Your Appointments</h2>
        <button className="btn-primary" onClick={fetchAppointments}>
          Refresh
        </button>
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
                  <td>
                    <span className="type-tag">
                      {apt.appointment_type.split("_").join(" ")}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusClass(apt.status)}`}>
                      {apt.status}
                    </span>
                  </td>
                  <td>
                    {renderMeetingCell(apt)}
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