import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Navigate } from "react-router";
import { Login, Profile } from "./pages";
import store, { persistor } from "./store";
import { PersistGate } from "redux-persist/integration/react";
import { Provider } from "react-redux";
import { useSelector } from "react-redux";
import { RootState } from "./store";

import './index.css';

function RequireAuth({ children, redirectTo }: { children: any, redirectTo: string}) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account ? children : <Navigate to={redirectTo} />;
}

export default function App() {
    return (
        <Provider store={store}>
            <PersistGate persistor={persistor} loading={null}>
                <Router>
                    <div>
                        <Routes>
                            <Route path="/login" element={<Login/>} />
                            <Route path="/"
                                   element={
                                        <RequireAuth redirectTo="/login">
                                            <Profile />
                                        </RequireAuth>
                                   } />
                        </Routes>
                    </div>
                </Router>
            </PersistGate>
        </Provider>
    );
}
