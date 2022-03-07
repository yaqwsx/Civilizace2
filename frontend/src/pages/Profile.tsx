import React from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router";
import authSlice from "../store/slices/auth";

const Profile = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const handleLogout = () => {
        dispatch(authSlice.actions.logout());
        navigate("/login");
    };
    return (
        <div className="w-full h-screen">
        <div className="w-full p-6">
            <button
                onClick={handleLogout}
                className="rounded p-2 w-32 bg-red-700 text-white"
                >
                Odhlásit se
            </button>
        </div>
            <div className="w-full h-full text-center items-center">
                <p className="self-center my-auto">Welcome</p>
            </div>
        </div>
    );
};

export default Profile;
