import React from "react";
import type { ChangeEvent, FormEvent } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "../styles/register.css";
import axios from "axios";
import toast from "react-hot-toast";
import { useDispatch } from "react-redux";
import { setUserInfo } from "../redux/reducers/rootSlice";
import { jwtDecode } from "jwt-decode";
import fetchData from "../helper/apiCall.ts";

axios.defaults.baseURL = import.meta.env.VITE_SERVER_DOMAIN;

interface FormDetails {
  email: string;
  password: string;
}

interface JwtPayload {
  userId: string;
}

const Login: React.FC = ()=> {
  const dispatch = useDispatch();
  const [formDetails, setFormDetails] = React.useState<FormDetails>({
    email: "",
    password: "",
  });

  const navigate = useNavigate();

  const inputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setFormDetails({
      ...formDetails,
      [name]: value,
    });
  };
    const formSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    try {
        e.preventDefault();
        const { email, password } = formDetails;

        if (!email || !password) {
        toast.error("Input field should not be empty");
        return;
        } else if (password.length < 5) {
        toast.error("Password must be at least 5 characters long");
        return;
        }

        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const { data } = await toast.promise(
        axios.post("/auth/login", formData, {
            headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            },
        }),
        {
            loading: "Logging in...",
            success: "Login successfully",
            error: "Unable to login user",
        }
        );

        localStorage.setItem("token", data.token);

        const decoded: JwtPayload = jwtDecode(data.token);
        dispatch(setUserInfo(decoded.userId));
        getUser(decoded.userId);
    } catch (error) {
        console.error(error);
    }
    };

  const getUser = async (_id: string): Promise<void> => {
    try {
      const temp = await fetchData(`/users/me`);
      dispatch(setUserInfo(temp));
      navigate("/");
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <section className="register-section flex-center">
      <div className="register-container flex-center">
        <h2 className="form-heading">Sign In</h2>

        <form onSubmit={formSubmit} className="register-form">
          <input
            type="email"
            name="email"
            className="form-input"
            placeholder="Enter your email"
            value={formDetails.email}
            onChange={inputChange}
          />

          <input
            type="password"
            name="password"
            className="form-input"
            placeholder="Enter your password"
            value={formDetails.password}
            onChange={inputChange}
          />

          <button type="submit" className="btn form-btn">
            sign in
          </button>
        </form>

        <p>
          Not a user?{" "}
          <NavLink className="login-link" to="/register">
            Register
          </NavLink>
        </p>
      </div>
    </section>
  );
}

export default Login;