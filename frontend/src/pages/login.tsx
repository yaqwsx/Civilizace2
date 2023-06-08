import axios from "axios";
import { useFormik } from "formik";
import { useState } from "react";
import { ThreeDots } from "react-loader-spinner";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router";
import * as Yup from "yup";
import { ErrorMessage } from "../elements/messages";
import authSlice from "../store/slices/auth";
import { AccountResponse } from "../types";

function Login() {
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const handleLogin = (username: string, password: string) => {
        axios
            .post<AccountResponse>(
                `${process.env.REACT_APP_API_URL}/auth/login/`,
                {
                    username,
                    password,
                }
            )
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
                console.error(err);
                setLoading(false);
                if (err.response && err.response.status === 401) {
                    setMessage("Nesprávné jméno nebo heslo");
                } else {
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
            username: Yup.string()
                .trim()
                .required("Uživatelské jméno je vyžadováno"),
            password: Yup.string().trim().required("Heslo je vyžadováno"),
        }),
        validateOnChange: false,
        validateOnBlur: false,
    });

    return (
        <div className="mx-auto w-full md:w-1/2">
            <div className="rounded border bg-white shadow">
                <div className="border-b p-3">
                    <h5 className="font-bold uppercase text-gray-600">
                        Přihlásit se
                    </h5>
                </div>
                <div className="p-5">
                    <form onSubmit={formik.handleSubmit}>
                        <div
                            id="div_id_username"
                            className="mb-6 md:flex md:items-center"
                        >
                            <div className="md:w-1/3">
                                <label
                                    htmlFor="id_username"
                                    className="requiredField mb-1 block pr-4 font-bold text-gray-500 md:mb-0 md:text-right"
                                >
                                    Uživatelské jméno
                                </label>
                                {formik.errors.username ? (
                                    <div className="pr-4 text-right text-sm text-red-700">
                                        {formik.errors.username}
                                    </div>
                                ) : null}
                            </div>
                            <div className="field md:w-2/3">
                                <input
                                    id="username"
                                    type="text"
                                    placeholder="Uživatelské jméno"
                                    name="username"
                                    value={formik.values.username}
                                    onChange={formik.handleChange}
                                    onBlur={formik.handleBlur}
                                />
                            </div>
                        </div>
                        <div
                            id="div_id_password"
                            className="mb-6 md:flex md:items-center"
                        >
                            <div className="md:w-1/3">
                                <label
                                    htmlFor="id_password"
                                    className="requiredField mb-1 block pr-4 font-bold text-gray-500 md:mb-0 md:text-right"
                                >
                                    Heslo
                                </label>
                                {formik.errors.password ? (
                                    <div className="pr-4 text-right text-sm text-red-700">
                                        {formik.errors.password}
                                    </div>
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
                                    onBlur={formik.handleBlur}
                                />
                            </div>
                        </div>

                        {message ? (
                            <ErrorMessage>{message}</ErrorMessage>
                        ) : null}

                        <button
                            className="focus:shadow-outline w-full rounded bg-purple-500 py-2 px-4 font-bold text-white shadow hover:bg-purple-400 focus:outline-none"
                            type="submit"
                        >
                            <div className="mx-auto inline-block">
                                {loading ? (
                                    <ThreeDots height="100%" color="white" />
                                ) : (
                                    "Přihlásit se"
                                )}
                            </div>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default Login;
