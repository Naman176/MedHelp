import React, { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { List, AutoSizer } from "react-virtualized";
import type { ListRowProps } from "react-virtualized";
import fetchData from "../helper/apiCall";
import { setDoctors } from "../redux/reducers/rootSlice";
import type { Doctor, UserInfo } from "../types";
import "../styles/doctors.css";
import { getDoctors } from "../redux/selectors/rootSelectors";

const Doctors: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const doctors = useSelector(getDoctors);
  const [loading, setLoading] = useState(false);

  const getAllDoctors = async () => {
    try {
      setLoading(true);
      const response = await fetchData("/doctors/");
      
      const mappedDoctors: Doctor[] = response.map((doc: any) => ({
        id: doc.id,
        userId: doc.user_id,
        specialization: doc.specialization,
        licenseNumber: doc.license_number,
        degreeUploadUrl: doc.degree_upload_url,
        bio: doc.bio,
        yearsOfExperience: doc.years_of_experience,
        consultationFee: doc.consultation_fee,
        isAvailable: doc.is_available,
        user: {
          id: doc.user.id,
          fullName: doc.user.full_name, 
          email: doc.user.email,
          profilePic: doc.user.profile_pic || doc.user.profilePic,
        } as UserInfo
      }));

      dispatch(setDoctors(mappedDoctors));
    } catch (error) {
      console.error("Failed to fetch doctors", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  if (doctors.length === 0) {
    getAllDoctors();
  }
}, [doctors.length]);

  const rowRenderer = ({ index, key, style }: ListRowProps) => {
    const doctor = doctors[index];
    if (!doctor) return null;

    return (
      <div key={key} style={style} className="doctor-row-wrapper">
        <div className="doctor-card">
          <div className="doc-info-main">
            <img 
              src={doctor.user.profilePic || "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"} 
              alt="Doctor" 
              className="doc-avatar"
            />
            <div className="doc-details">
              <h3>Dr. {doctor.user.fullName}</h3>
              <p className="specialization">{doctor.specialization}</p>
              <p className="experience">{doctor.yearsOfExperience} Years Experience</p>
            </div>
          </div>
          
          <div className="doc-stats">
            <span className="fee">Fee: {doctor.consultationFee} Rs</span>
            <span className={`availability ${doctor.isAvailable ? 'online' : 'offline'}`}>
              {doctor.isAvailable ? "Available" : "Busy"}
            </span>
          </div>

          <button 
            className="btn-book" 
            onClick={() => navigate(`/book-appointment/${doctor.id}`)}
          >
            Book Appointment
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="doctors-page">
      <div className="page-header">
        <h2>Verified Specialists</h2>
        <p>Browse through our network of certified medical professionals.</p>
      </div>
      {loading && (
        <div className="loading-banner">
          Loading doctors, please wait...
        </div>
      )}

      {doctors.length > 0 && <div className="virtual-list-container">
        <AutoSizer>
          {({ height, width }) => (
            <List
              width={width}
              height={height}
              rowCount={doctors.length}
              rowHeight={130} 
              rowRenderer={rowRenderer}
            />
          )}
        </AutoSizer>
      </div>}
    </div>
  );
};

export default Doctors;