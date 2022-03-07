import React from "react";
import { Navigate, Route, RouteProps } from "react-router";
import { useSelector } from "react-redux";
import { RootState } from "../store";

const ProtectedRoute = (props: RouteProps) => {
    const auth = useSelector((state: RootState) => state.auth);

    if (auth.account) {
        if (props.path === "/login") {
            return <Navigate to={"/"} />;
        }
        return <Route {...props} />;
    } else if (!auth.account) {
        return <Navigate to={"/login"} />;
    } else {
        return <div>Not found</div>;
    }
};

export default ProtectedRoute;
