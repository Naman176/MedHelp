import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import _ from "lodash";
import { useSelector } from "react-redux";
import { getUserInfo } from "../redux/selectors/rootSelectors";

interface Props {
  children: ReactNode;
}

export const Protected = ({ children }: Props) => {
  const userInfo = useSelector(getUserInfo);

  if (!userInfo) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export const Public = ({ children }: Props) => {
  const userInfo = useSelector(getUserInfo);

  if (!userInfo || _.isEmpty(userInfo)) {
    return <>{children}</>;
  }

  return <Navigate to="/" replace />;
};

export const Admin = ({ children }: Props) => {
  const userInfo = useSelector(getUserInfo);

  if (!userInfo) {
    return <Navigate to="/" replace />;
  }

  const userRole = userInfo.role;

  if (userRole === "admin") {
    return <>{children}</>;
  }

  return <Navigate to="/" replace />;
};
