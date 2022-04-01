import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, NavLink } from "react-router-dom";
import { Navigate } from "react-router";
import { Login, Profile } from "./pages";
import store, { persistor } from "./store";
import authSlice from "./store/slices/auth";
import { PersistGate } from "redux-persist/integration/react";
import { Provider } from "react-redux";
import { useSelector } from "react-redux";
import { RootState } from "./store";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { faCity, faChartLine, faHistory } from '@fortawesome/free-solid-svg-icons'
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { DashboardMenu, Dashboard } from "./pages/Dashboard";
import { Generation, GenerationMenu } from "./pages/Generation";
import './index.css';

import { Forbidden } from "./pages/Forbidden";

type RequireAuthProps = {
    children: JSX.Element | JSX.Element[];
};
function RequireAuth({ children }: RequireAuthProps) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account ? <>{children}</> : <Navigate to="/login" />;
}

type RequireOrgProps = {
    children: JSX.Element | JSX.Element[];
};
function RequireOrg({ children }: RequireOrgProps) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account?.user?.isOrg ? <>{children}</> : <Navigate to="/forbidden" />;
}


function IconHamburger() {
    return <svg className="fill-current h-3 w-3" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <title>Menu</title>
        <path d="M0 3h20v2H0V3zm0 6h20v2H0V9zm0 6h20v2H0v-2z" />
    </svg>;
}

function IconArrowDown() {
    return <svg className="pl-2 h-2" version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 129 129"
        xmlnsXlink="http://www.w3.org/1999/xlink" enableBackground="new 0 0 129 129">
        <g>
            <path
                d="m121.3,34.6c-1.6-1.6-4.2-1.6-5.8,0l-51,51.1-51.1-51.1c-1.6-1.6-4.2-1.6-5.8,0-1.6,1.6-1.6,4.2 0,5.8l53.9,53.9c0.8,0.8 1.8,1.2 2.9,1.2 1,0 2.1-0.4 2.9-1.2l53.9-53.9c1.7-1.6 1.7-4.2 0.1-5.8z" />
        </g>
    </svg>
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
                </span>
                <IconArrowDown />
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
                className="flex place-items-end float-right px-3 py-2 border rounded text-gray-500 border-gray-600 hover:text-gray-900 hover:border-teal-500 appearance-none focus:outline-none">
                <IconHamburger />
            </button>
        </div>
    </>
}

type MenuRowProps = {
    children?: JSX.Element | JSX.Element[];
}
function MenuRow(props: MenuRowProps) {
    return (<ul className="w-full list-reset lg:flex flex-1 items-center px-4 md:px-0 border-gray-600 border-b-2 lg:border-none">
        {props.children}
    </ul>);
}

type MenuItemProps = {
    name: string;
    icon: IconDefinition;
    path: string;
};
function MenuItem(props: MenuItemProps) {
    let className = ({ isActive }: { isActive: boolean; }) => {
        let classes = "block py-1 md:py-3 pl-1 align-middle no-underline hover:text-gray-900 border-b-2 hover:border-orange-500";
        if (isActive) {
            classes += " text-orange-500 border-orange-500";
        }
        else {
            classes += " text-gray-500 border-gray-500";
        }
        return classes;
    };

    return (<li className="mr-6 my-2 md:my-0">
        <NavLink
            to={props.path}
            className={className}>
            <FontAwesomeIcon icon={props.icon}
                className="fas fa-fw mr-3 text-orange-500" />
            <span className="pb-1 md:pb-0 text-sm">{props.name}</span>
        </NavLink>
    </li>);
}

function OrgMenu() {
    const account = useSelector((state: RootState) => state.auth.account);

    if (account === null || !account.user.isOrg) {
        return <></>;
    }

    return <MenuRow>
        <MenuItem name="Přehled týmů" icon={faChartLine} path="dashboard" />
        <MenuItem name="Generace" icon={faHistory} path="generations" />
    </MenuRow>;
}

function ApplicationMenu() {
    return (<>
        <OrgMenu />
        <Routes>
            <Route path="/dashboard" element={<DashboardMenu />}></Route>
            <Route path="/generations" element={<GenerationMenu />}></Route>
        </Routes>
    </>);
}

function ApplicationHeader() {
    return (
        <nav id="header" className="bg-white w-full z-10 top-0 shadow">
            <div className="w-full container mx-auto flex flex-wrap items-center mt-0 pt-3 pb-3 md:pb-0">
                <div className="w-1/2 pl-2 md:pl-0">
                    <a className="flex-grow text-gray-900 text-base xl:text-xl no-underline hover:no-underline font-bold" href="/">
                        <FontAwesomeIcon icon={faCity}
                            className="text-orange-500 pr-3" /> Příběh civilizace
                    </a>
                </div>

                <div className="w-1/2 pr-0">
                    <div className="relative inline-block float-right">
                        <UserMenu />
                    </div>
                </div>

                <div className="w-full flex-grow lg:items-center lg:w-auto hidden lg:block mt-2 lg:mt-0 bg-white z-20">
                    <ApplicationMenu />
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
                            <Route path="/login" element={<Login/>} />
                            <Route path="/forbidden" element={<Forbidden/>}/>
                            {/* Why such a weird way? Well, only <Route> is
                                allowed as a children of Routes. Also, we could
                                build the structure of the application into
                                data structure and construct this automatically,
                                however, Civilizace seems small enough to just
                                specify this directly */}
                            <Route path="/"
                                element={
                                    <RequireAuth>
                                        <Navigate to={"/dashboard"} />
                                    </RequireAuth>
                                } />
                            <Route path="/dashboard"
                                element={
                                    <RequireAuth>
                                        <Dashboard/>
                                    </RequireAuth>} />
                            <Route path="/generations"
                                element={
                                    <RequireOrg>
                                        <Generation/>
                                    </RequireOrg>} />
                        </Routes>
                    </AppFrame>
                </Router>
            </PersistGate>
        </Provider>
    );
}
