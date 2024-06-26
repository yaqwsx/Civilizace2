import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
    faBook,
    faChartLine,
    faCity,
    faCubesStacked,
    faFlask,
    faHistory,
    faIndustry,
    faMountainCity,
    faQrcode,
    faSkullCrossbones,
    faStickyNote,
    faTimeline,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { Provider, useDispatch, useSelector } from "react-redux";
import { Navigate } from "react-router";
import {
    Link,
    NavLink,
    Route,
    BrowserRouter as Router,
    Routes,
    useNavigate,
} from "react-router-dom";
import { PersistGate } from "redux-persist/integration/react";
import { ScannerDispatcher, ScannerNavigator } from "./elements/scanner";
import "./index.css";
import { Login } from "./pages";
import { Dashboard, DashboardMenu } from "./pages/dashboard";
import { MapAgenda, MapMenu } from "./pages/map";
import { Turns, TurnsMenu } from "./pages/turns";
import { Vyroba, VyrobaMenu } from "./pages/vyrobas";
import store, { RootState, persistor } from "./store";
import authSlice from "./store/slices/auth";

import { useAtom } from "jotai";
import { RequireAuth, RequireOrg, RequireSuperOrg } from "./elements";
import { UnfinishedActionBar } from "./elements/action";
import { useTeamIdFromUrl } from "./elements/team";
import { ToastProvider } from "./elements/toast";
import { FinishAction } from "./pages/action";
import { ActionLog } from "./pages/actionlog";
import { Announcements, AnnouncementsMenu } from "./pages/announcements";
import { AnyAction } from "./pages/anyaction";
import { menuShownAtom } from "./pages/atoms";
import { Forbidden } from "./pages/forbidden";
import { GodMode, GodModeMenu } from "./pages/godmode";
import { InfoScreen } from "./pages/info";
import { MapDiffView } from "./pages/mapdiff";
import { QrReader } from "./pages/qr_reader";
import { ScanTest } from "./pages/scanTest";
import { Tasks, TasksMenu } from "./pages/tasks";
import { Tech, TechMenu } from "./pages/techs";

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

function MenuRow(props: JSX.ElementChildrenAttribute) {
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

    if (account === null || !account.user.is_org) {
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
            <MenuItemT name="Výroby" icon={faIndustry} path="vyrobas/" />
            <MenuItemT name="Technologie" icon={faFlask} path="techs/" />
            <MenuItemT name="Mapa" icon={faMountainCity} path="map/" />
            <MenuItemT name="Úkoly" icon={faCubesStacked} path="tasks/" />
            <MenuItemT
                name="Vývěska"
                icon={faStickyNote}
                path="announcements/"
            />
            <MenuItemT name="QR čtečka" icon={faQrcode} path="qrreader/" />
            {account.user.is_superuser ? (
                <>
                    <MenuItemT
                        name="Zadání akce"
                        icon={faBook}
                        path="actions/"
                    />
                    <MenuItemT
                        name="God mode"
                        icon={faSkullCrossbones}
                        path="godmode/"
                    />
                    <MenuItemT
                        name="Log akcí"
                        icon={faTimeline}
                        path="actionlog/"
                    />
                </>
            ) : null}
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
                <Route path="/vyrobas" element={<VyrobaMenu />} />
                <Route path="/techs" element={<TechMenu />} />
                <Route path="/tasks/*" element={<TasksMenu />} />
                <Route path="/map/*" element={<MapMenu />} />
                <Route path="/godmode" element={<GodModeMenu />} />
                <Route
                    path="/announcements/*"
                    element={<AnnouncementsMenu />}
                />
                <Route path="/qrreader" element={null} />
            </Routes>
        </>
    );
}

function ApplicationHeader() {
    const [menuExpanded, setMenuExpanded] = useAtom(menuShownAtom);

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
                        className="mb-32 w-full px-2 leading-normal text-gray-800 md:mt-2 md:px-0"
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

function Error404() {
    return <h1>Stránka nenalezena.</h1>;
}

function AppPages() {
    const account = useSelector((state: RootState) => state.auth.account);

    return (
        <AppFrame>
            <ScannerNavigator />
            {account?.user?.is_org ? <UnfinishedActionBar /> : <></>}
            <Routes>
                <Route
                    path="/dashboard/*"
                    element={
                        <RequireAuth>
                            <Dashboard />
                        </RequireAuth>
                    }
                />
                <Route
                    path="*"
                    element={
                        <RequireOrg>
                            <OrgPages />
                        </RequireOrg>
                    }
                />
            </Routes>
        </AppFrame>
    );
}

function OrgPages() {
    return (
        <Routes>
            <Route path="/vyrobas" element={<Vyroba />} />
            <Route path="/techs" element={<Tech />} />
            <Route path="/map" element={<MapAgenda />} />
            <Route path="/tasks/*" element={<Tasks />} />
            <Route path="/announcements/*" element={<Announcements />} />
            <Route path="/turns" element={<Turns />} />
            <Route path="/actions/team/:actionId" element={<FinishAction />} />
            <Route path="/qrreader" element={<QrReader />} />
            <Route
                path="*"
                element={
                    <RequireSuperOrg>
                        <SuperOrgPages />
                    </RequireSuperOrg>
                }
            />
        </Routes>
    );
}

function SuperOrgPages() {
    return (
        <Routes>
            <Route path="/actions" element={<AnyAction />} />
            <Route path="/godmode" element={<GodMode />} />
            <Route path="/actionlog" element={<ActionLog />} />
            <Route path="*" element={<Error404 />} />
        </Routes>
    );
}

export default function App() {
    return (
        <Provider store={store}>
            <PersistGate persistor={persistor} loading={null}>
                <Router>
                    <ToastProvider />
                    <ScannerDispatcher>
                        <Routes>
                            <Route
                                path="/"
                                element={<Navigate to={"/dashboard"} />}
                            />

                            <Route
                                path="/login"
                                element={
                                    <AppFrame>
                                        <Login />
                                    </AppFrame>
                                }
                            />
                            <Route
                                path="/forbidden"
                                element={
                                    <AppFrame>
                                        <Forbidden />
                                    </AppFrame>
                                }
                            />
                            <Route
                                path="/info"
                                element={
                                    <RequireOrg>
                                        <InfoScreen />
                                    </RequireOrg>
                                }
                            />
                            <Route
                                path="/mapdiff"
                                element={
                                    <RequireOrg>
                                        <MapDiffView />
                                    </RequireOrg>
                                }
                            />
                            <Route path="scanner" element={<ScanTest />} />
                            <Route path="*" element={<AppPages />} />
                        </Routes>
                    </ScannerDispatcher>
                </Router>
            </PersistGate>
        </Provider>
    );
}
