import React, { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "../styles/register.css";
import axios from "axios";
import toast from "react-hot-toast";

axios.defaults.baseURL = import.meta.env.VITE_SERVER_DOMAIN as string;

interface RegisterFormDetails {
  firstname: string;
  lastname: string;
  email: string;
  password: string;
  confpassword: string;
}

const Register: React.FC = () => {
//   const [file, setFile] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [formDetails, setFormDetails] = useState<RegisterFormDetails>({
    firstname: "",
    lastname: "",
    email: "",
    password: "",
    confpassword: "",
  });

  const navigate = useNavigate();

  const inputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setFormDetails({
      ...formDetails,
      [name]: value,
    });
  };

  const formSubmit = async (
    e: FormEvent<HTMLFormElement>
  ): Promise<void> => {
    try {
      e.preventDefault();

      const { firstname, lastname, email, password, confpassword } =
        formDetails;

      if (!firstname || !lastname || !email || !password || !confpassword) {
        toast.error("Input field should not be empty");
        return;
      } else if (firstname.length < 3) {
        toast.error("First name must be at least 3 characters long");
        return;
      } else if (lastname.length < 3) {
        toast.error("Last name must be at least 3 characters long");
        return;
      } else if (password.length < 5) {
        toast.error("Password must be at least 5 characters long");
        return;
      } else if (password !== confpassword) {
        toast.error("Passwords do not match");
        return;
      }

      await toast.promise(
        axios.post("/user/register", {
          full_name: `${firstname} ${lastname}`,
          email,
          password,
          // pic: file,
        }),
        {
          loading: "Registering user...",
          success: "User registered successfully",
          error: "Unable to register user",
        }
      );

      navigate("/login");
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <section className="register-section flex-center">
      <div className="register-container flex-center">
        <h2 className="form-heading">Sign Up</h2>

        <form onSubmit={formSubmit} className="register-form">
          <input
            type="text"
            name="firstname"
            className="form-input"
            placeholder="Enter your first name"
            value={formDetails.firstname}
            onChange={inputChange}
          />

          <input
            type="text"
            name="lastname"
            className="form-input"
            placeholder="Enter your last name"
            value={formDetails.lastname}
            onChange={inputChange}
          />

          <input
            type="email"
            name="email"
            className="form-input"
            placeholder="Enter your email"
            value={formDetails.email}
            onChange={inputChange}
          />

          {/* File upload (optional later)
          <input
            type="file"
            name="profile-pic"
            className="form-input"
            onChange={(e) => setFile(e.target.files?.[0]?.name || "")}
          />
          */}

          <input
            type="password"
            name="password"
            className="form-input"
            placeholder="Enter your password"
            value={formDetails.password}
            onChange={inputChange}
          />

          <input
            type="password"
            name="confpassword"
            className="form-input"
            placeholder="Confirm your password"
            value={formDetails.confpassword}
            onChange={inputChange}
          />

          <button
            type="submit"
            className="btn form-btn"
            disabled={loading}
          >
            sign up
          </button>
        </form>

        <p>
          Already a user?{" "}
          <NavLink className="login-link" to="/login">
            Log in
          </NavLink>
        </p>
      </div>
    </section>
  );
}

export default Register;