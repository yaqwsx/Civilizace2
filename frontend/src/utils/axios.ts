import axios from "axios";
import createAuthRefreshInterceptor from "axios-auth-refresh";
import store from "../store";
import authSlice from "../store/slices/auth";
import { AccountResponse } from "../types";

const axiosService = axios.create({
    baseURL: process.env.REACT_APP_API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

axiosService.interceptors.request.use(async (config) => {
    const { token } = store.getState().auth;

    if (token !== null) {
        // @ts-ignore
        config.headers.Authorization = "Bearer " + token;
        // @ts-ignore
        console.debug(
            "[Request]",
            config.baseURL ?? "" + config.url,
            JSON.stringify(token)
        );
    }
    return config;
});

axiosService.interceptors.response.use(
    (res) => {
        // @ts-ignore
        // console.debug('[Response]', res.config.baseURL + res.config.url, res.status, res.data);
        return Promise.resolve(res);
    },
    (err) => {
        console.debug(
            "[Response error]",
            err.config.baseURL + err.config.url,
            err.response.status,
            err.response.data
        );
        return Promise.reject(err);
    }
);

// @ts-ignore
const refreshAuthLogic = async (failedRequest) => {
    console.log(store.getState().auth);
    const { refreshToken } = store.getState().auth;
    if (refreshToken !== null) {
        return axios
            .post<AccountResponse>(
                "/auth/refresh/",
                {
                    refresh: refreshToken,
                },
                {
                    baseURL: process.env.REACT_APP_API_URL,
                }
            )
            .then((resp) => {
                const { access, refresh } = resp.data;
                failedRequest.response.config.headers.Authorization =
                    "Bearer " + access;
                store.dispatch(
                    authSlice.actions.setAuthTokens({
                        token: access,
                        refreshToken: refresh,
                    })
                );
            })
            .catch((err) => {
                if (err.response && err.response.status === 401) {
                    store.dispatch(authSlice.actions.logout());
                }
            });
    }
    // There is no token, logout
    store.dispatch(authSlice.actions.logout());
};

createAuthRefreshInterceptor(axiosService, refreshAuthLogic);

export function fetcher<T = any>(url: string) {
    return axiosService.get<T>(url).then((res) => res.data);
}

export default axiosService;
