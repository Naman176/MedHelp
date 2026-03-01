import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { postFormData } from "../helper/apiCall";
import "../styles/applyAsDoctor.css";

const ApplyAsDoctor: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    specialization: "",
    license_number: "",
    experience: "",
    consultation_fee: "",
    bio: "",
  });

  const [degreeFile, setDegreeFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setDegreeFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!degreeFile) {
      setError("Please upload your degree certificate.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = new FormData();
      data.append("specialization", formData.specialization);
      data.append("license_number", formData.license_number);
      data.append("experience", formData.experience);
      data.append("consultation_fee", formData.consultation_fee);
      data.append("bio", formData.bio);
      data.append("degree_file", degreeFile);

      await postFormData("/doctors/apply", data);

      setSuccess("Application submitted successfully!");
      setTimeout(() => navigate("/"), 2000);

    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Failed to submit application");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="apply-doctor-page">
      <h2>Apply as a Doctor</h2>

      <form onSubmit={handleSubmit} className="apply-doctor-form">
        <input
          type="text"
          name="specialization"
          placeholder="Specialization"
          required
          value={formData.specialization}
          onChange={handleChange}
        />

        <input
          type="text"
          name="license_number"
          placeholder="License Number"
          required
          value={formData.license_number}
          onChange={handleChange}
        />

        <input
          type="number"
          name="experience"
          placeholder="Years of Experience"
          required
          value={formData.experience}
          onChange={handleChange}
        />

        <input
          type="number"
          name="consultation_fee"
          placeholder="Consultation Fee"
          required
          value={formData.consultation_fee}
          onChange={handleChange}
        />

        <textarea
          name="bio"
          placeholder="Short Bio (optional)"
          value={formData.bio}
          onChange={handleChange}
        />
        <label className="file-upload-label">
          Upload Degree Certificate (PDF/JPG/PNG):
        </label>
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          required
          onChange={handleFileChange}
        />

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Submitting..." : "Submit Application"}
        </button>
      </form>
    </div>
  );
};

export default ApplyAsDoctor;