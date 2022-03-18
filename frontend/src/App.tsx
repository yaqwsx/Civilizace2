import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Navigate } from "react-router";
import { Login, Profile } from "./pages";
import store, { persistor } from "./store";
import authSlice from "./store/slices/auth";
import { PersistGate } from "redux-persist/integration/react";
import { Provider } from "react-redux";
import { useSelector } from "react-redux";
import { RootState } from "./store";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCity } from '@fortawesome/free-solid-svg-icons'
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";

import './index.css';

function RequireAuth({ children, redirectTo }: { children: any, redirectTo: string }) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account ? children : <Navigate to={redirectTo} />;
}

function UserMenu() {
    const account = useSelector((state: RootState) => state.auth.account);
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const [expanded, setExpanded] = useState(false);

    const handleLogout = () => {
        dispatch(authSlice.actions.logout());
        setExpanded(false);
        navigate("/login");
    };

    const toggleExpanded = () => {
        setExpanded(!expanded);
    }

    if (!account?.user) {
        return <></>
    }

    return <>
        <div className="relative text-sm">
            <button className="flex items-center focus:outline-none mr-3"
                onClick={toggleExpanded}>
                <span className="md:inline-block">
                    Příhlášen jako {account.user.username}
                    {/* {% if request.user.lastname %}
                            ({{request.user.firstname}} {{request.user.lastname}})
                        {% endif %} */}
                </span>
                <svg className="pl-2 h-2" version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 129 129"
                    xmlnsXlink="http://www.w3.org/1999/xlink" enableBackground="new 0 0 129 129">
                    <g>
                        <path
                            d="m121.3,34.6c-1.6-1.6-4.2-1.6-5.8,0l-51,51.1-51.1-51.1c-1.6-1.6-4.2-1.6-5.8,0-1.6,1.6-1.6,4.2 0,5.8l53.9,53.9c0.8,0.8 1.8,1.2 2.9,1.2 1,0 2.1-0.4 2.9-1.2l53.9-53.9c1.7-1.6 1.7-4.2 0.1-5.8z" />
                    </g>
                </svg>
            </button>
            {
                expanded ?
                    <div id="userMenu"
                        className="bg-white rounded shadow-md mt-12 lg:mt-6 absolute top-0 right-0 min-w-full overflow-auto z-30">
                        <ul className="list-reset">
                            <li><button onClick={handleLogout}
                                className="px-4 py-2 block text-gray-900 no-underline hover:no-underline">
                                Odhlásit se</button>
                            </li>
                        </ul>
                    </div>
                    : <></>
            }
        </div>

        <div className="block lg:hidden pr-4">
            <button onClick={toggleExpanded}
                className="flex place-items-end px-3 py-2 border rounded text-gray-500 border-gray-600 hover:text-gray-900 hover:border-teal-500 appearance-none focus:outline-none">
                <svg className="fill-current h-3 w-3" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <title>Menu</title>
                    <path d="M0 3h20v2H0V3zm0 6h20v2H0V9zm0 6h20v2H0v-2z" />
                </svg>
            </button>
        </div>
    </>
}

function ApplicationHeader() {
    return (<nav id="header" className="bg-white w-full z-10 top-0 shadow">
        <div className="w-full container mx-auto flex flex-wrap items-center mt-0 pt-3 pb-3 md:pb-0">
            <a className="flex-grow text-gray-900 text-base xl:text-xl no-underline hover:no-underline font-bold" href="/">
                <FontAwesomeIcon icon={faCity}
                    className="text-orange-500 pr-3" /> Příběh civilizace
            </a>

            <div className="w-1/2 pr-0">
                <div className="relative inline-block float-right">
                    <UserMenu />
                </div>
            </div>
        </div>
    </nav>)
}

type AppFrameProps = {
    children?: JSX.Element | JSX.Element[];
};
function AppFrame(props: AppFrameProps) {
    return <>
        <div className="bg-gray-100 font-sans leading-normal tracking-normal flex flex-col min-h-screen">
            <ApplicationHeader />
            <div className="container w-full mx-auto pt-1 flex-grow" id="content">
                <div id="mainContent" className="w-full px-2 md:px-0 md:mt-2 mb-16 text-gray-800 leading-normal">
                    {props.children}
                </div>
            </div>

            <footer className="bg-white border-t border-gray-400 shadow">
                <div className="container max-w-md mx-auto flex py-8">
                </div>
            </footer>
        </div>
    </>;
}

export default function App() {
    return (
        <Provider store={store}>
            <PersistGate persistor={persistor} loading={null}>
                <Router>
                    <AppFrame>
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/"
                                element={
                                    <RequireAuth redirectTo="/login">
                                        <Profile />
                                    </RequireAuth>
                                } />
                        </Routes>
                    </AppFrame>
                </Router>
            </PersistGate>
        </Provider>
    );
}
