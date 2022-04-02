import React, { useState } from "react";
import * as Yup from "yup";
import { useFormik } from "formik";
import { useDispatch } from "react-redux";
import axios from "axios";
import { useNavigate } from "react-router";
import authSlice from "../store/slices/auth";
import { ThreeDots } from "react-loader-spinner"
import {ErrorMessage} from "../elements/messages"

function Login() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const handleLogin = (username: string, password: string) => {
        axios
            .post(`${process.env.REACT_APP_API_URL}/auth/login/`, { username, password })
            .then((res) => {
                dispatch(
                    authSlice.actions.setAuthTokens({
                        token: res.data.access,
                        refreshToken: res.data.refresh,
                    })
                );
                dispatch(authSlice.actions.setAccount(res.data));
                setLoading(false);
                setMessage("");
                navigate("/", { replace: true });
            })
            .catch((err) => {
                setLoading(false);
                if (err.response && err.response.status === 401) {
                    setMessage("Nesprávné jméno nebo heslo");
                }
                else {
                    setMessage("Neočekávaná chyba: " + err.toString());
                }
            });
    };

    const formik = useFormik({
        initialValues: {
            username: "",
            password: "",
        },
        onSubmit: (values) => {
            setLoading(true);
            handleLogin(values.username, values.password);
        },
        validationSchema: Yup.object({
            username: Yup.string().trim().required("Uživatelské jméno je vyžadováno"),
            password: Yup.string().trim().required("Heslo je vyžadováno"),
        }),
        validateOnChange: false,
        validateOnBlur: false
    });

    return (<div className="w-full md:w-1/2 mx-auto">
        <div className="bg-white border rounded shadow">
            <div className="border-b p-3">
                <h5 className="font-bold uppercase text-gray-600">Přihlásit se</h5>
            </div>
            <div className="p-5">
                <form onSubmit={formik.handleSubmit}>


                    <div id="div_id_username" className="md:flex md:items-center mb-6">
                        <div className="md:w-1/3">
                            <label htmlFor="id_username" className="block text-gray-500 font-bold md:text-right mb-1 md:mb-0 pr-4 requiredField">
                                Uživatelské jméno
                            </label>
                            {formik.errors.username ? <div className="text-right text-sm pr-4 text-red-700">{formik.errors.username} </div> : null}
                        </div>
                        <div className="field md:w-2/3">
                            <input
                                id="username"
                                type="text"
                                placeholder="Uživatelské jméno"
                                name="username"
                                value={formik.values.username}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur} />
                        </div>
                    </div>
                    <div id="div_id_password" className="md:flex md:items-center mb-6">
                        <div className="md:w-1/3">
                            <label htmlFor="id_password" className="block text-gray-500 font-bold md:text-right mb-1 md:mb-0 pr-4 requiredField">
                                Heslo
                            </label>
                            {formik.errors.password ? (
                                <div className="text-right text-sm pr-4 text-red-700">{formik.errors.password} </div>
                            ) : null}
                        </div>
                        <div className="field md:w-2/3">
                            <input
                                id="password"
                                type="password"
                                placeholder="Heslo"
                                name="password"
                                value={formik.values.password}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur} />
                        </div>
                    </div>

                    {
                    message
                        ? <ErrorMessage>{message}</ErrorMessage>
                        : null
                    }

                    <button className="w-full shadow bg-purple-500 hover:bg-purple-400 focus:shadow-outline focus:outline-none text-white font-bold py-2 px-4 rounded" type="submit">
                        <div className="mx-auto inline-block">
                        {
                            loading
                                ? <ThreeDots height="100%" color="white"/>
                                : "Přihlásit se"
                        }
                        </div>
                    </button>
                </form>
            </div>
        </div>
    </div>);
}

export default Login;
