import { useEffect, useState } from "react";
import fetchData, { putData } from "../helper/apiCall";
import type { Appointment } from "../types";
import toast from "react-hot-toast";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "../redux/store";
import {
  setPendingAppointments,
  removePendingAppointment
} from "../redux/reducers/pendingAppointmentSlice";

import "../styles/PendingAppointment.css"
export const PendingAppointments: React.FC = () => {
  const dispatch = useDispatch();

  const { appointments, initialized } = useSelector(
    (state: RootState) => state.pendingAppointments
  );

  const [loadingIds, setLoadingIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialized) return; // prevent refetch

    const fetchAppointments = async () => {
      setLoading(true);
      try {
        const res = await fetchData("/appointments/pendingAppointments");
        dispatch(setPendingAppointments(res));
      } catch (err) {
        console.error(err);
        toast.error("Failed to load appointments");
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, [dispatch, initialized]);

  const updateStatus = async (
    id: string,
    status: "CONFIRMED" | "REJECTED"
  ) => {
    setLoadingIds(prev => new Set(prev).add(id));

    try {
      await putData(`/appointments/${id}/status`, { status });

      dispatch(removePendingAppointment(id));

      if (status === "CONFIRMED") toast.success("Appointment approved");
      else toast("Appointment rejected", { icon: "⚠️" });

    } catch (err) {
      console.error(err);
      toast.error("Failed to update appointment");
    } finally {
      setLoadingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  if (loading) return <p className="loading-state">Loading appointments...</p>;

  if (!appointments.length)
    return <p className="empty-state">No appointments to approve</p>;

  return (
    <div className="pending-container">
      <h2 className="pending-title">
        Pending Appointments ({appointments.length})
      </h2>

      {appointments.map((appt: Appointment) => (
        <div key={appt.id} className="appointment-card">

          <div className="appointment-row">
            <span className="appointment-label">Patient:</span>
            {appt.patient?.full_name || "Unknown"}
          </div>

          <div className="appointment-row">
            <span className="appointment-label">Date:</span>
            {appt.appointment_date}
          </div>

          <div className="appointment-row">
            <span className="appointment-label">Time:</span>
            {appt.appointment_time}
          </div>

          {loadingIds.has(appt.id) ? (
            <p className="approving-text">Processing...</p>
          ) : (
            <div className="appointment-actions">
              <button
                className="approve-button"
                onClick={() => updateStatus(appt.id, "CONFIRMED")}
              >
                Approve
              </button>

              <button
                className="reject-button"
                onClick={() => updateStatus(appt.id, "REJECTED")}
              >
                Reject
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};