import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSelector } from "react-redux";
import {
    Navigate,
    NavLink,
    Route,
    Routes,
    useNavigate,
    useParams,
} from "react-router-dom";
import {
    Button,
    Card,
    CiviMarkdown,
    classNames,
    LoadingOrError,
} from "../elements";
import { useTeam, useTeams } from "../elements/team";
import { RootState } from "../store";
import { Team } from "../types";
import {
    faUsers,
    faBriefcase,
    faCalendar,
    faCogs,
    faWarehouse,
    faWheatAwn,
} from "@fortawesome/free-solid-svg-icons";
import useSWR from "swr";
import axiosService, { fetcher } from "../utils/axios";
import { combineErrors } from "../utils/error";
import { EntityTag, useTeamTechs } from "../elements/entities";
import { sortTechs } from "./techs";
import { useState } from "react";
import { toast } from "react-toastify";

function MiddleTeamMenu(props: { teams: Team[] }) {
    let className = ({ isActive }: { isActive: boolean }) => {
        let classes =
            "block py-1  align-middle no-underline hover:text-gray-900 border-b-2 hover:border-orange-500 align-middle";
        if (isActive) {
            classes += " text-orange-500 border-orange-500";
        } else {
            classes += " text-gray-500 border-gray-500";
        }
        return classes;
    };

    return (
        <ul className="list-reset w-full flex-1 items-center border-b-2 border-gray-600 px-4 md:px-0 lg:flex lg:border-none">
            {props.teams.map((t) => (
                <li key={t.id} className="my-2 mr-6 list-none md:my-0">
                    <NavLink to={`/dashboard/${t.id}`} className={className}>
                        <div
                            className={`inline-block h-5 w-5 align-middle bg-${t.color} mr-2 rounded`}
                        />
                        <span className="pb-1 text-sm md:pb-0">{t.name}</span>
                    </NavLink>
                </li>
            ))}
        </ul>
    );
}

function DashboardMenuImpl() {
    const user = useSelector((state: RootState) => state.auth.account?.user);
    const { teamId } = useParams();
    const { teams } = useTeams();

    if (!teams) return null;

    let subLinks = [
        { url: "", name: "Přehled" },
        { url: "tasks", name: "Úkoly" },
        { url: "messages", name: "Zprávy" },
    ];

    let className = ({ isActive }: { isActive: boolean }) => {
        let classes =
            "block py-1 px-3 align-middle no-underline hover:text-gray-900 border-b-2 hover:border-orange-500";
        if (isActive) {
            classes += " text-orange-500 border-orange-500";
        } else {
            classes += " text-gray-500 border-gray-500";
        }
        return classes;
    };

    return (
        <>
            {user?.isOrg ? <MiddleTeamMenu teams={teams} /> : null}
            <ul className="list-reset w-full flex-1 items-center border-b-2 border-gray-600 px-4 md:px-0 lg:flex lg:border-none">
                {subLinks.map((l) => (
                    <li key={l.url} className="my-2 mr-6 list-none md:my-0">
                        <NavLink
                            to={`/dashboard/${teamId}/${l.url}`}
                            className={className}
                        >
                            {/* <FontAwesomeIcon
                                icon={props.icon}
                                className="fas fa-fw mr-3 text-orange-500"
                            /> */}
                            <span className="pb-1 text-sm md:pb-0">
                                {l.name}
                            </span>
                        </NavLink>
                    </li>
                ))}
            </ul>
        </>
    );
}

export function DashboardMenu() {
    return (
        <Routes>
            <Route path=":teamId/*" element={<DashboardMenuImpl />} />
        </Routes>
    );
}

export function Dashboard() {
    const user = useSelector((state: RootState) => state.auth.account?.user);
    const { teams, error: teamError } = useTeams();

    if (!teams) {
        return (
            <LoadingOrError
                loading={!teams && !teamError}
                error={teamError}
                message="Nemůžu se spojit se serverem. Zkouším znovu"
            />
        );
    }

    let firstTeam = teams[0];

    return (
        <Routes>
            <Route
                path=""
                element={
                    user?.isOrg ? (
                        <Navigate to={`${firstTeam.id}/`} />
                    ) : (
                        <Navigate to={`${user?.team.id}`} />
                    )
                }
            />
            <Route path=":teamId/" element={<TeamOverview />} />
            <Route path=":teamId/tasks" element={<TeamTasks />} />
            <Route path=":teamId/messages" element={<TeamMessages />} />
            <Route path="*" element={<Navigate to="" />} />
        </Routes>
    );
}

function TeamOverview() {
    const { teamId } = useParams();
    const { team, error: teamError, loading: teamLoading } = useTeam(teamId);
    const { data, error: dataError } = useSWR<any>(
        () => (teamId ? `game/teams/${teamId}/dashboard` : null),
        fetcher
    );

    if (!team || !data) {
        return (
            <LoadingOrError
                loading={teamLoading || (!data && !dataError)}
                error={combineErrors([teamError, dataError])}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    return (
        <>
            <h1>Přehled týmu {team.name}</h1>

            {data?.announcements?.length ? (
                <>
                    <h2>Nová oznámení</h2>
                    <AnnouncementList
                        announcements={data.announcements}
                        deletable={true}
                    />
                </>
            ) : null}

            <div className="section w-full">
                <h2 className="text-xl" id="section-1">
                    Souhrnné informace
                </h2>
            </div>

            <div className="flex w-full flex-wrap">
                <Card label="Populace" color={team.color} icon={faUsers}>
                    {data.population.spec}/{data.population.all}
                    <div className="w-full text-center text-sm text-gray-400">
                        (nespecializovaných/celkem)
                    </div>
                </Card>

                <Card
                    label="Dostupná práce"
                    color={team.color}
                    icon={faBriefcase}
                >
                    {data.work}
                </Card>

                <Card label="Kolo" color={team.color} icon={faCalendar}>
                    Právě probíhá {data.round}. kolo
                </Card>
            </div>

            <div className="section w-full">
                <h2 className="text-xl" id="section-1">
                    Ekonomika
                </h2>

                <div className="flex w-full flex-wrap">
                    <Card
                        label="Právě zkoumané technologie"
                        color={team.color}
                        icon={faCogs}
                    >
                        {data.researchingTechs.length ? (
                            <ul className="list-disc text-left">
                                {data.researchingTechs.map((t: any) => (
                                    <li key={t.id}>{t.name}</li>
                                ))}
                            </ul>
                        ) : (
                            <span>Právě nezkoumáte žádné technologie.</span>
                        )}
                    </Card>

                    <Card
                        label="Dostupné produkce"
                        color={team.color}
                        icon={faWarehouse}
                    >
                        {data.productions.length ? (
                            <ul className="list-disc text-left">
                                {data.productions.map((p: any) => (
                                    <li key={p[0]}>
                                        <EntityTag id={p[0]} quantity={p[1]} />
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <span>Nevlastníte žádné produkce</span>
                        )}
                    </Card>

                    <Card
                        label="Materiály ve skladu"
                        color={team.color}
                        icon={faWarehouse}
                    >
                        {data.storage.length ? (
                            <ul className="list-disc text-left">
                                {data.storage.map((p: any) => (
                                    <li key={p[0]}>
                                        <EntityTag id={p[0]} quantity={p[1]} />
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <span>Sklad je prázdný</span>
                        )}
                    </Card>
                    <Card
                        label="Zásobování centra"
                        color={team.color}
                        icon={faWheatAwn}
                    >
                        Tady je obsah
                    </Card>
                </div>
            </div>
        </>
    );
}

function TeamTasks() {
    const { teamId } = useParams();
    const { team, error: teamError, loading: teamLoading } = useTeam(teamId);
    const {
        techs,
        loading: techsLoading,
        error: techsError,
    } = useTeamTechs(team);

    if (!team || !techs) {
        return (
            <LoadingOrError
                loading={teamLoading || techsLoading}
                error={teamError || techsError}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    const researchingTechs = sortTechs(
        Object.values(techs).filter(
            (t) => t.status === "researching" && t?.assignedTask
        )
    );

    return (
        <>
            <h1>Přehled aktivních úkolů pro tým {team.name}</h1>
            {researchingTechs.length ? (
                <>
                    {researchingTechs.map((t) => (
                        <div className="my-2 w-full rounded bg-white p-3 py-2 px-4 shadow">
                            <h3 className="mt-0">
                                Úkol '{t.assignedTask?.name}' pro technologii '
                                {t.name}'
                            </h3>
                            <p>
                                <CiviMarkdown>
                                    {t.assignedTask?.teamDescription}
                                </CiviMarkdown>
                            </p>
                        </div>
                    ))}
                </>
            ) : (
                <p>Právě nemáte zadané žádné úkoly</p>
            )}
        </>
    );
}

function TeamMessages() {
    const { teamId } = useParams();
    const { team, error: teamError, loading: teamLoading } = useTeam(teamId);
    const { data, error: dataError } = useSWR<any>(
        () => (teamId ? `game/teams/${teamId}/announcements` : null),
        fetcher
    );

    if (!team || !data) {
        return (
            <LoadingOrError
                loading={teamLoading || (!data && !dataError)}
                error={combineErrors([teamError, dataError])}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    return (
        <>
            <h1>Přehled zpráv pro tým {team.name}</h1>
            {data?.length == 0 ? (
                <p>Zatím vám nepřišla žádná oznámení</p>
            ) : (
                <AnnouncementList deletable={false} announcements={data} />
            )}
        </>
    );
}

function announcementColor(type: string) {
    return {
        normal: "bg-blue-200",
        important: "bg-orange-200",
    }[type];
}

function Announcement(props: {
    type: string;
    id: number;
    content: string;
    read: boolean;
    deletable: boolean;
}) {
    const user = useSelector((state: RootState) => state.auth.account?.user);
    const [submitting, setSubmitting] = useState(false);
    const [deleted, setDeleted] = useState(false);

    if (!user || deleted) return null;

    let className = classNames(
        "mb-4 w-full rounded bg-white py-2 px-4 shadow md:flex",
        announcementColor(props.type)
    );

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<any, any>(`/announcements/${props.id}/read/`)
            .then((data) => {
                setSubmitting(false);
                if (props.deletable) setDeleted(true);
            })
            .catch((error) => {
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };

    return (
        <div className={className}>
            <div className="m-2 inline-block w-full md:w-auto md:flex-grow">
                <CiviMarkdown>{props.content}</CiviMarkdown>
            </div>
            {!props.read && !user.isOrg ? (
                <div className="inline-block w-full md:w-auto">
                    <Button
                        label={
                            !submitting
                                ? "Označit jako přečtené"
                                : "Označuji jako přečtené"
                        }
                        className="mx-0 my-0 w-full"
                        disabled={submitting}
                        onClick={handleSubmit}
                    />
                </div>
            ) : null}
        </div>
    );
}

function AnnouncementList(props: { announcements: any; deletable: boolean }) {
    return (
        <>
            {props.announcements.map((a: any) => (
                <Announcement key={a.id} deletable={props.deletable} {...a} />
            ))}
        </>
    );
}
