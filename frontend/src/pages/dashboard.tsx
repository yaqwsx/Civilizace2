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
import { Card, CiviMarkdown, LoadingOrError } from "../elements";
import { useTeam, useTeams } from "../elements/team";
import { RootState } from "../store";
import { Team } from "../types";
import {
    faUsers,
    faBriefcase,
    faCalendar,
    faCogs,
    faWarehouse,
    faWheatAwn
} from "@fortawesome/free-solid-svg-icons";
import useSWR from "swr";
import { fetcher } from "../utils/axios";
import { combineErrors } from "../utils/error";
import { EntityTag, useTeamTechs } from "../elements/entities";
import { sortTechs } from "./techs";

function MiddleTeamMenu(props: { teams: Team[] }) {
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
        <ul className="list-reset w-full flex-1 items-center border-b-2 border-gray-600 px-4 md:px-0 lg:flex lg:border-none">
            {props.teams.map((t) => (
                <li key={t.id} className="my-2 mr-6 list-none md:my-0">
                    <NavLink to={`/dashboard/${t.id}`} className={className}>
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
            "block py-1 md:py-3 pl-1 align-middle no-underline hover:text-gray-900 border-b-2 hover:border-orange-500";
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
    const { data, error: dataError } = useSWR<any>(() => teamId ? `game/teams/${teamId}/dashboard` : null, fetcher);

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

            <div className="section w-full">
                <h2 className="text-xl" id="section-1">
                    Souhrnné informace
                </h2>
            </div>

            <div className="flex w-full flex-wrap">
                <Card label="Populace" color={team.color} icon={faUsers}>
                    {data.population.spec}/{data.population.all}
                    <div className="w-full text-center text-sm text-gray-400">(nespecializovaných/celkem)</div>
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
                <Card label="Právě zkoumané technologie" color={team.color} icon={faCogs}>
                    {
                        data.researchingTechs.length ? <ul className="list-disc text-left">
                            {
                                data.researchingTechs.map((t: any) => <li key={t.id}>
                                    {t.name}
                                </li>)
                            }
                        </ul> : <span>Právě nezkoumáte žádné technologie.</span>
                    }
                </Card>

                <Card
                    label="Dostupné produkce"
                    color={team.color}
                    icon={faWarehouse}
                >
                    {
                        data.productions.length ? <ul className="list-disc text-left">
                            {
                                data.productions.map((p: any) => <li key={p[0]} >
                                    <EntityTag id={p[0]} quantity={p[1]}/>
                                </li>)
                            }
                        </ul> : <span>Nevlastníte žádné produkce</span>
                    }
                </Card>

                <Card
                    label="Materiály ve skladu"
                    color={team.color}
                    icon={faWarehouse}
                >
                    {
                        data.storage.length ? <ul className="list-disc text-left">
                            {
                                data.storage.map((p: any) => <li key={p[0]} >
                                <EntityTag id={p[0]} quantity={p[1]}/>
                            </li>)
                            }
                        </ul> : <span>Sklad je prázdný</span>
                    }
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
    const { techs, loading: techsLoading, error: techsError } = useTeamTechs(team);

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
        Object.values(techs).filter((t) => t.status === "researching" && t?.assignedTask)
    );

    return <>
    <h1>Přehled aktivních úkolů pro tým {team.name}</h1>
    {
        researchingTechs.length ? <>
            {
                researchingTechs.map(t => <div className="w-full p-3 rounded bg-white py-2 px-4 shadow my-2">
                    <h3 className="mt-0">Úkol '{t.assignedTask?.name}' pro technologii '{t.name}'</h3>
                    <p>
                        <CiviMarkdown>
                            {t.assignedTask?.teamDescription}
                        </CiviMarkdown>
                    </p>
                </div>)
            }
        </> : <p>Právě nemáte zadané žádné úkoly</p>
    }
    </>;
}

function TeamMessages() {
    const { teamId } = useParams();
    const { team, error: teamError, loading: teamLoading } = useTeam(teamId);

    if (!team) {
        return (
            <LoadingOrError
                loading={teamLoading}
                error={teamError}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    return <h1>Přehled zpráv pro tým {team.name}</h1>;
}
