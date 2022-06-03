import React, { useCallback, useContext, useEffect, useState } from "react";
import {
    BrowserRouter as Router,
    Routes,
    Route,
    NavLink,
    Link,
} from "react-router-dom";
import { Navigate } from "react-router";
import { Login } from "./pages";
import store, { persistor } from "./store";
import authSlice from "./store/slices/auth";
import { PersistGate } from "redux-persist/integration/react";
import { Provider } from "react-redux";
import { useSelector } from "react-redux";
import { RootState } from "./store";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
    faCity,
    faChartLine,
    faHistory,
    faIndustry,
    faFlask,
    faCubesStacked,
    faStickyNote,
    faMountainCity,
    faTicket,
} from "@fortawesome/free-solid-svg-icons";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { ScannerContext, ScannerDispatcher } from "./pages/scanner";
import { DashboardMenu, Dashboard } from "./pages/dashboard";
import { Turns, TurnsMenu } from "./pages/turns";
import { VyrobaMenu, Vyroba } from "./pages/vyrobas";
import { MapMenu, MapAgenda } from "./pages/map";
import "./index.css";

import { Forbidden } from "./pages/forbidden";
import { Tech, TechMenu } from "./pages/techs";
import { Tasks, TasksMenu } from "./pages/tasks";
import { Vouchers, VouchersMenu } from "./pages/vouchers";
import { Announcements, AnnouncementsMenu } from "./pages/announcements";
import { ToastProvider } from "./elements/toast";
import { useTeamIdFromUrl } from "./elements/team";

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
    return auth.account?.user?.isOrg ? (
        <>{children}</>
    ) : (
        <Navigate to="/forbidden" />
    );
}

function IconHamburger() {
    return (
        <svg
            className="h-3 w-3 fill-current"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
        >
            <title>Menu</title>
            <path d="M0 3h20v2H0V3zm0 6h20v2H0V9zm0 6h20v2H0v-2z" />
        </svg>
    );
}

function IconArrowDown() {
    return (
        <svg
            className="h-2 pl-2"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 129 129"
            xmlnsXlink="http://www.w3.org/1999/xlink"
            enableBackground="new 0 0 129 129"
        >
            <g>
                <path d="m121.3,34.6c-1.6-1.6-4.2-1.6-5.8,0l-51,51.1-51.1-51.1c-1.6-1.6-4.2-1.6-5.8,0-1.6,1.6-1.6,4.2 0,5.8l53.9,53.9c0.8,0.8 1.8,1.2 2.9,1.2 1,0 2.1-0.4 2.9-1.2l53.9-53.9c1.7-1.6 1.7-4.2 0.1-5.8z" />
            </g>
        </svg>
    );
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
    };

    if (!account?.user) {
        return <></>;
    }

    return (
        <>
            <div className="relative text-sm">
                <button
                    className="mr-3 flex items-center focus:outline-none"
                    onClick={toggleExpanded}
                >
                    <span className="md:inline-block">
                        Příhlášen jako {account.user.username}
                    </span>
                    <IconArrowDown />
                </button>
                {expanded ? (
                    <div
                        id="userMenu"
                        className="absolute top-0 right-0 z-30 mt-12 min-w-full overflow-auto rounded bg-white shadow-md lg:mt-6"
                    >
                        <ul className="list-reset list-none">
                            <li>
                                <button
                                    onClick={handleLogout}
                                    className="block px-4 py-2 text-gray-900 no-underline hover:no-underline"
                                >
                                    Odhlásit se
                                </button>
                            </li>
                        </ul>
                    </div>
                ) : (
                    <></>
                )}
            </div>
        </>
    );
}

type MenuRowProps = {
    children?: JSX.Element | JSX.Element[];
};
function MenuRow(props: MenuRowProps) {
    return (
        <ul className="list-reset w-full flex-1 items-center border-b-2 border-gray-600 px-4 md:px-0 lg:flex lg:border-none">
            {props.children}
        </ul>
    );
}

type MenuItemProps = {
    name: string;
    icon: IconDefinition;
    path: string;
};
function MenuItem(props: MenuItemProps) {
    let className = ({ isActive }: { isActive: boolean }) => {
        let classes =
            "block py-1 md:py-3 pl-1 align-middle no-underline hover:text-gray-900 border-b-2 hover:border-orange-500";
        if (isActive) {
            classes += " text-orange-500 border-orange-500";
        } else {
            classes += " text-gray-500 border-gray-500";
        }
        return classes;
    };

    return (
        <li className="my-2 mr-6 list-none md:my-0">
            <NavLink to={props.path} className={className}>
                <FontAwesomeIcon
                    icon={props.icon}
                    className="fas fa-fw mr-3 text-orange-500"
                />
                <span className="pb-1 text-sm md:pb-0">{props.name}</span>
            </NavLink>
        </li>
    );
}

function OrgMenu() {
    const account = useSelector((state: RootState) => state.auth.account);
    const [teamId] = useTeamIdFromUrl();

    if (account === null || !account.user.isOrg) {
        return null;
    }

    let MenuItemT = (props: MenuItemProps) => {
        let { path, ...otherProps } = props;
        return (
            <MenuItem
                path={teamId ? `${path}#team=${teamId}` : path}
                {...otherProps}
            />
        );
    };

    return (
        <MenuRow>
            <MenuItemT
                name="Přehled týmů"
                icon={faChartLine}
                path="dashboard/"
            />
            <MenuItemT name="Kola" icon={faHistory} path="turns/" />
            <MenuItemT name="Směnky" icon={faTicket} path="vouchers/"/>
            <MenuItemT name="Výroby" icon={faIndustry} path="vyrobas/" />
            <MenuItemT name="Technologie" icon={faFlask} path="techs/" />
            <MenuItemT name="Mapa" icon={faMountainCity} path="map/" />
            <MenuItemT name="Úkoly" icon={faCubesStacked} path="tasks/" />
            <MenuItemT
                name="Vývěska"
                icon={faStickyNote}
                path="announcements/"
            />
        </MenuRow>
    );
}

function ApplicationMenu() {
    return (
        <>
            <OrgMenu />
            <Routes>
                <Route path="/dashboard/*" element={<DashboardMenu />} />
                <Route path="/turns" element={<TurnsMenu />} />
                <Route path="/vouchers" element={<VouchersMenu/>}/>
                <Route path="/vyrobas" element={<VyrobaMenu />} />
                <Route path="/techs" element={<TechMenu />} />
                <Route path="/tasks/*" element={<TasksMenu />} />
                <Route path="/map/*" element={<MapMenu />} />
                <Route
                    path="/announcements/*"
                    element={<AnnouncementsMenu />}
                />
            </Routes>
        </>
    );
}

function ApplicationHeader() {
    const [menuExpanded, setMenuExpanded] = useState(false);

    let toggleExpanded = () => setMenuExpanded(!menuExpanded);

    return (
        <nav id="header" className="top-0 z-10 w-full bg-white shadow">
            <div className="container mx-auto mt-0 flex w-full flex-wrap items-center pt-3 pb-3 md:pb-0">
                <div className="w-1/2 pl-2 md:pl-0">
                    <Link
                        className="flex-grow text-base font-bold text-gray-900 no-underline hover:no-underline xl:text-xl"
                        to="/"
                    >
                        <FontAwesomeIcon
                            icon={faCity}
                            className="pr-3 text-orange-500"
                        />{" "}
                        Příběh civilizace
                    </Link>
                </div>

                <div className="flex w-1/2 pr-0 md:block">
                    <div className="relative float-right mr-3 inline-block md:mr-0">
                        <UserMenu />
                    </div>
                    <div className="block pr-4 lg:hidden">
                        <button
                            onClick={toggleExpanded}
                            className="float-right flex appearance-none place-items-end rounded border border-gray-600 px-3 py-2 text-gray-500 hover:border-teal-500 hover:text-gray-900 focus:outline-none"
                        >
                            <IconHamburger />
                        </button>
                    </div>
                </div>

                <div
                    className={`z-20 mt-2 ${
                        menuExpanded ? "" : "hidden"
                    } w-full flex-grow bg-white md:flex-none lg:mt-0 lg:block lg:w-auto lg:items-center`}
                >
                    <ApplicationMenu />
                </div>
            </div>
        </nav>
    );
}

type AppFrameProps = {
    children?: JSX.Element | JSX.Element[];
};
function AppFrame(props: AppFrameProps) {
    return (
        <>
            <div className="flex min-h-screen flex-col bg-gray-100 font-sans leading-normal tracking-normal">
                <ApplicationHeader />
                <div
                    className="container mx-auto w-full flex-grow pt-1"
                    id="content"
                >
                    <div
                        id="mainContent"
                        className="mb-16 w-full px-2 leading-normal text-gray-800 md:mt-2 md:px-0"
                    >
                        {props.children}
                    </div>
                </div>

                <footer className="border-t border-gray-400 bg-white shadow">
                    <div className="container mx-auto flex max-w-md py-8"></div>
                </footer>
            </div>
        </>
    );
}

function ScannerNavigator() {
    const navigate = useNavigate();
    const {subscribe, unsubscribe} = useContext(ScannerContext);

    const navigator = useCallback((items: string[]) => {
        let args: string[] = [];
        let page = null;
        items.forEach((item) => {
            if (item.startsWith("tym-")) {
                args.push(`team=${item}`);
                return;
            }
            if (item.startsWith("vyr-")) {
                args.push(`entity=${item}`);
                page = "vyrobas";
                return;
            }
            if (item.startsWith("tech-")) {
                args.push(`entity=${item}`);
                page = "techs";
                return;
            }
        });
        if (page) {
            console.log("Navigating to " + `${page}#${args.join("&")}`);
            navigate(page);
            window.location.hash = `#${args.join("&")}`;
        }
    }, [navigate]);

    useEffect(() => {
        subscribe(navigator);
        return () => {unsubscribe(navigator)}
    }, [subscribe, unsubscribe, navigate])
    return null;
}

export default function App() {
    return (
        <Provider store={store}>
            <PersistGate persistor={persistor} loading={null}>
                <Router>
                    <AppFrame>
                        <ToastProvider />
                        <ScannerDispatcher>
                            <ScannerNavigator/>
                            <Routes>
                                <Route path="/login" element={<Login />} />
                                <Route
                                    path="/forbidden"
                                    element={<Forbidden />}
                                />
                                {/* Why such a weird way? Well, only <Route> is
                                allowed as a children of Routes. Also, we could
                                build the structure of the application into
                                data structure and construct this automatically,
                                however, Civilizace seems small enough to just
                                specify this directly */}
                                <Route
                                    path="/"
                                    element={
                                        <RequireAuth>
                                            <Navigate to={"/dashboard"} />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/dashboard/*"
                                    element={
                                        <RequireAuth>
                                            <Dashboard />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/vyrobas"
                                    element={
                                        <RequireAuth>
                                            <Vyroba />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/techs"
                                    element={
                                        <RequireAuth>
                                            <Tech />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/map"
                                    element={
                                        <RequireAuth>
                                            <MapAgenda />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/vouchers"
                                    element={
                                        <RequireAuth>
                                            <Vouchers />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/tasks/*"
                                    element={
                                        <RequireAuth>
                                            <Tasks />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/announcements/*"
                                    element={
                                        <RequireAuth>
                                            <Announcements />
                                        </RequireAuth>
                                    }
                                />
                                <Route
                                    path="/turns"
                                    element={
                                        <RequireOrg>
                                            <Turns />
                                        </RequireOrg>
                                    }
                                />
                            </Routes>
                        </ScannerDispatcher>
                    </AppFrame>
                </Router>
            </PersistGate>
        </Provider>
    );
}
