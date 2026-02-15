import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface JwtPayload {
  isAdmin: boolean;
}

export const Protected = ({ children }: Props) => {
  const token = localStorage.getItem("token");

  if (!token) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export const Public = ({ children }: Props) => {
  const token = localStorage.getItem("token");

  if (!token) {
    return <>{children}</>;
  }

  return <Navigate to="/" replace />;
};

export const Admin = ({ children }: Props) => {
  const token = localStorage.getItem("token");

  if (!token) {
    return <Navigate to="/" replace />;
  }

  const user = jwtDecode<JwtPayload>(token);

  if (user.isAdmin) {
    return <>{children}</>;
  }

  return <Navigate to="/" replace />;
};