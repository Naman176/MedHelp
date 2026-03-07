export interface UserInfo {
  fullName?: string;
  email?: string;
  profilePic?: string;
  role?: "user" | "doctor" | "admin";
}

export interface AuthProps {
  isLoggedIn: boolean;
  userInfo: UserInfo | null;
  handleLogout?: () => void;
}

export interface Appointment {
  id: string;
  doctor_id: string;
  patient_id: string;
  appointment_date: string;
  appointment_time: string;
  status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'PENDING'; // Using specific strings for better safety
  appointment_type: 'VIRTUAL' | 'IN_PERSON';
  meeting_link?: string;
}

export interface Doctor {
  id: string;
  userId: string;
  specialization: string;
  licenseNumber: string;
  degreeUploadUrl: string;
  bio?: string;
  yearsOfExperience: number;
  consultationFee: number;
  isAvailable: boolean;
  user: UserInfo;
}

export interface DoctorRequest {
  id: string;
  userId: string;
  specialization: string;
  experience: number;
  consultationFee: number;
  degreeUrl: string;
  fullName: string;
  email: string;
}

export interface RejectPayload {
  reason: string;
}

export interface UserAdminView {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: "INFO" | "SUCCESS" | "WARNING" | "ERROR" | "REMINDER";
  is_read: boolean;
  created_at: string;
}