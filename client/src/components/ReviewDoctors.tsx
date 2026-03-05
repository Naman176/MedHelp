import React, { useEffect, useState } from "react";
import fetchData, { patchData } from "../helper/apiCall";
import toast from "react-hot-toast";
import { Check, X, ExternalLink } from "lucide-react";
import "../styles/reviewDoctors.css";

import type { DoctorRequest } from "../types";

const ReviewDoctors: React.FC = () => {
  const [requests, setRequests] = useState<DoctorRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPendingDoctors = async () => {
    try {
      const data = await fetchData("/admin/doctors/pending"); 
      
      const mapped: DoctorRequest[] = data.map((doc: any) => ({
        id: doc.id,
        userId: doc.user_id,
        specialization: doc.specialization,
        experience: doc.years_of_experience,
        consultationFee: doc.consultation_fee,
        degreeUrl: doc.degree_upload_url,
        fullName: `${doc.user.full_name}`,
        email: doc.user.email,
      }));

      setRequests(mapped);
    } catch (error) {
      toast.error("Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingDoctors();
  }, []);

  const handleApprove = async (doctorId: string) => {
    const loadingToast = toast.loading("Verifying doctor...");
    try {
      await patchData(`/admin/doctors/${doctorId}/verify`, {});
      toast.success("Doctor verified successfully", { id: loadingToast });
      
      // Remove from UI
      setRequests((prev) => prev.filter((req) => req.id !== doctorId));
    } catch (error) {
      toast.error("Verification failed", { id: loadingToast });
    }
  };

  const handleReject = async (doctorId: string) => {
    const reason = window.prompt("Please enter the reason for rejection:");
    
    if (!reason) {
      return toast.error("A reason is required to reject an application.");
    }

    const loadingToast = toast.loading("Rejecting application...");
    try {
      await patchData(`/admin/doctors/${doctorId}/reject`, {'reason': reason});
      toast.success("Application rejected and doctor notified", { id: loadingToast });
      
      // Remove from UI
      setRequests((prev) => prev.filter((req) => req.id !== doctorId));
    } catch (error) {
      toast.error("Rejection failed", { id: loadingToast });
    }
  };

  if (loading) return <div className="loader">Loading applications...</div>;

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h2>Pending Doctor Applications</h2>
        <span className="count-badge">{requests.length} Requests</span>
      </div>

      <div className="table-responsive">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Doctor Name</th>
              <th>Specialization</th>
              <th>Exp.</th>
              <th>Fee</th>
              <th>Documents</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.length > 0 ? (
              requests.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <div className="td-name">
                      <span className="name">{doc.fullName}</span>
                      <span className="email">{doc.email}</span>
                    </div>
                  </td>
                  <td>{doc.specialization}</td>
                  <td>{doc.experience} Yrs</td>
                  <td>${doc.consultationFee}</td>
                  <td>
                    <a href={doc.degreeUrl} target="_blank" rel="noreferrer" className="view-link">
                      <ExternalLink size={14} /> View Degree
                    </a>
                  </td>
                  <td className="actions-cell">
                    <button 
                      className="btn-icon btn-approve" 
                      onClick={() => handleApprove(doc.id)}
                      title="Approve"
                    >
                      <Check size={18} />
                    </button>
                    <button 
                      className="btn-icon btn-reject" 
                      onClick={() => handleReject(doc.id)}
                      title="Reject"
                    >
                      <X size={18} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="no-data">No pending applications found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ReviewDoctors;