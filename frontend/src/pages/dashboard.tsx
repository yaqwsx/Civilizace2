import {
    faBarcode,
    faBriefcase,
    faCalendar,
    faCogs,
    faFlag,
    faMasksTheater,
    faScrewdriverWrench,
    faSeedling,
    faShieldAlt,
    faTags,
    faUsers,
    faWarehouse,
    faWheatAwn,
} from "@fortawesome/free-solid-svg-icons";
import _ from "lodash";
import { useState } from "react";
import QRCode from "react-qr-code";
import { useSelector } from "react-redux";
import { NavLink, Navigate, Route, Routes, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import useSWR from "swr";
import {
    Button,
    Card,
    CiviMarkdown,
    Dialog,
    LoadingOrError,
    RequireOrg,
    classNames,
} from "../elements";
import { EntityTag, useEntities, useTeamTechs } from "../elements/entities";
import { PrintStickers } from "../elements/printing";
import { useTeam, useTeamIdFromUrl, useTeams } from "../elements/team";
import { TurnCountdownSticker } from "../elements/turns";
import { RootState } from "../store";
import { Army, Sticker as StickerT, Team, TeamDashboard } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";
import { ArmyDescription } from "./map";
import { sortTechs } from "./techs";

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
        { url: "", name: "Přehled", orgOnly: false },
        { url: "tasks", name: "Úkoly", orgOnly: false },
        { url: "announcements", name: "Oznámení", orgOnly: false },
        { url: "stickers", name: "Samolepky", orgOnly: true },
    ];

    let accessibleSubLinks = user?.is_org
        ? subLinks
        : subLinks.filter((x) => !x.orgOnly);

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
            {user?.is_org ? <MiddleTeamMenu teams={teams} /> : null}
            <ul className="list-reset w-full flex-1 items-center border-b-2 border-gray-600 px-4 md:px-0 lg:flex lg:border-none">
                {accessibleSubLinks.map((l) => (
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
    useHideMenu();

    const user = useSelector((state: RootState) => state.auth.account?.user);
    const { teams, error: teamError } = useTeams();
    const [urlTeamId] = useTeamIdFromUrl();

    if (!teams) {
        return (
            <LoadingOrError
                error={teamError}
                message="Nemůžu se spojit se serverem. Zkouším znovu"
            />
        );
    }

    let firstTeam = teams[0];

    return (
        <>
            <TurnCountdownSticker />
            <Routes>
                <Route
                    path=""
                    element={
                        user?.is_org ? (
                            <Navigate
                                to={`${urlTeamId || firstTeam.id}/#team=${
                                    urlTeamId || firstTeam.id
                                }`}
                            />
                        ) : (
                            <Navigate to={`${user?.team?.id}`} />
                        )
                    }
                />
                <Route path=":teamId/" element={<TeamOverview />} />
                <Route path=":teamId/tasks" element={<TeamTasks />} />
                <Route
                    path=":teamId/announcements"
                    element={<TeamMessages />}
                />
                <Route
                    path=":teamId/stickers"
                    element={
                        <RequireOrg>
                            <TeamStickers />
                        </RequireOrg>
                    }
                />
                <Route path="*" element={<Navigate to="" />} />
            </Routes>
        </>
    );
}

function CardSection(props: { name: string; children?: any }) {
    return (
        <div className="section w-full">
            <h2 className="text-xl" id="section-1">
                {props.name}
            </h2>
            <div className="flex w-full flex-wrap">{props.children}</div>
        </div>
    );
}

function TeamOverview() {
    const { teamId } = useParams();
    const { team, error: teamError } = useTeam(teamId);
    const { data, error: dataError } = useSWR<TeamDashboard>(
        () => (teamId ? `game/teams/${teamId}/dashboard` : null),
        fetcher
    );
    const account = useSelector((state: RootState) => state.auth.account);

    if (!team || !data) {
        return (
            <LoadingOrError
                error={teamError || dataError}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    return (
        <>
            <h1>Přehled týmu {team.name}</h1>

            {data.announcements?.length ? (
                <>
                    <h2>Nová oznámení</h2>
                    <AnnouncementList
                        announcements={data.announcements}
                        deletable={true}
                    />
                </>
            ) : null}

            {account?.user?.is_org && !_.isNil(data.orginfo) ? (
                <CardSection name="Org menu">
                    <Card
                        label="Týmové skupiny"
                        color={team.color}
                        icon={faFlag}
                    >
                        <ul>
                            {data.orginfo.groups.map((id: string) => (
                                <li key={id}>
                                    <EntityTag id={id} />
                                </li>
                            ))}
                        </ul>
                    </Card>
                    <Card
                        label="Technologie vlastněné týmem"
                        color={team.color}
                        icon={faScrewdriverWrench}
                    >
                        <ul>
                            {data.orginfo.techs.map((id: string) => (
                                <li key={id}>
                                    <EntityTag id={id} />
                                </li>
                            ))}
                        </ul>
                    </Card>
                    <Card
                        label="Vlastnosti týmu"
                        color={team.color}
                        icon={faTags}
                    >
                        <ul>
                            {data.orginfo.attributes.map((id: string) => (
                                <li key={id}>
                                    <EntityTag id={id} />
                                </li>
                            ))}
                        </ul>
                    </Card>
                </CardSection>
            ) : null}

            <CardSection name="Souhrnné informace">
                <Card label="Populace" color={team.color} icon={faUsers}>
                    {data.specialres.obyvatels}/{data.specialres.population}
                    <div className="w-full text-center text-sm text-gray-400">
                        (nespecializovaných/celkem)
                    </div>
                </Card>

                <Card
                    label="Dostupná práce"
                    color={team.color}
                    icon={faBriefcase}
                >
                    {data.specialres.work}
                </Card>

                <Card label="Kolo" color={team.color} icon={faCalendar}>
                    {data.worldTurn == 0
                        ? "Hra ještě nezačala."
                        : data.worldTurn != data.teamTurn
                        ? "V tomto kole jste ještě nekrmili"
                        : "V tomto kole jste už krmili."}
                </Card>
                <Card
                    label="Dostupná kultura"
                    color={team.color}
                    icon={faMasksTheater}
                >
                    {data.specialres.culture}
                </Card>
            </CardSection>

            <CardSection name="Ekonomika">
                <Card
                    label="Právě zkoumané technologie"
                    color={team.color}
                    icon={faCogs}
                >
                    {data.researching.length ? (
                        <ul className="list-disc text-left">
                            {data.researching.map((t: any) => (
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
                    icon={faSeedling}
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
                    {data.granary.length ? (
                        <>
                            Maximálně bonusů: {data.feeding.casteCount}
                            <br />
                            Potřeba žetonů, aby nikdo neumřel:{" "}
                            {data.feeding.tokensRequired}
                            <br />
                            Potřeba žetonů pro spokojenost kasty:{" "}
                            {data.feeding.tokensPerCaste}
                            <ul className="list-disc text-left">
                                {data.granary.map(([prod, amount]) => {
                                    let missing =
                                        amount - data.feeding.tokensPerCaste;
                                    return (
                                        <li key={prod}>
                                            <EntityTag
                                                id={prod}
                                                quantity={amount}
                                            />{" "}
                                            (
                                            {missing < 0 ? (
                                                <span className="text-red-500">
                                                    {missing}
                                                </span>
                                            ) : (
                                                <span className="text-green-500">
                                                    +{missing}
                                                </span>
                                            )}
                                            )
                                        </li>
                                    );
                                })}
                            </ul>
                        </>
                    ) : (
                        <span>Zatím nezásobujete centrum</span>
                    )}
                </Card>
            </CardSection>

            <CardSection name="Armády">
                {data.armies.map((a: Army) => (
                    <Card
                        key={a.index}
                        label={`Armáda ${a.name} ${"✱".repeat(a.level)}`}
                        color={team.color}
                        icon={faShieldAlt}
                    >
                        <ArmyDescription army={a} />
                    </Card>
                ))}
            </CardSection>

            <CardSection name="Různé">
                <Card label="Krmení" color={team.color} icon={faBarcode}>
                    <QRCode
                        value={`krm-${team.id}`}
                        size={128}
                        className="m-10 mx-auto max-h-40"
                    />
                </Card>
            </CardSection>
        </>
    );
}

function TeamTasks() {
    const { teamId } = useParams();
    const { team, error: teamError } = useTeam(teamId);
    const { techs, error: techsError } = useTeamTechs(team);

    if (!team) {
        return (
            <LoadingOrError
                error={teamError}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    if (!techs) {
        return (
            <LoadingOrError
                error={techsError}
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
                        <div
                            key={t.id}
                            className="my-2 w-full rounded bg-white p-3 py-2 px-4 shadow"
                        >
                            <h3 className="mt-0">
                                Úkol '{t.assignedTask?.name}' pro technologii '
                                {t.name}'
                            </h3>
                            <CiviMarkdown>
                                {t.assignedTask?.teamDescription}
                            </CiviMarkdown>
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
    const { team, error: teamError } = useTeam(teamId);
    const { data, error: dataError } = useSWR<any>(
        () => (teamId ? `game/teams/${teamId}/announcements` : null),
        fetcher
    );

    if (!team || !data) {
        return (
            <LoadingOrError
                error={teamError || dataError}
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

export function announcementPalette(type: string) {
    return {
        normal: {
            color: "blue-500",
            border: "border-blue-500",
            bg: "bg-blue-200",
        },
        important: {
            color: "orange-500",
            border: "border-orange-500",
            bg: "bg-orange-200",
        },
        game: {
            color: "red-500",
            border: "border-red-500",
            bg: "bg-red-200",
        },
    }[type];
}

function Announcement(props: {
    type: string;
    id: number;
    content: string;
    read: boolean;
    deletable: boolean;
    appearDatetime: string;
    readBy?: string[];
}) {
    const user = useSelector((state: RootState) => state.auth.account?.user);
    const [submitting, setSubmitting] = useState(false);
    const [deleted, setDeleted] = useState(false);

    if (!user || deleted || !props.type) return null;

    let colors = announcementPalette(props.type);

    let className = classNames(
        "mb-4 rounded-b border-t-4 px-4 py-3 shadow-md",
        colors?.border,
        colors?.bg
    );

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<{}>(`/announcements/${props.id}/read/`)
            .then(() => {
                setSubmitting(false);
                if (props.deletable) setDeleted(true);
            })
            .catch((error) => {
                console.error("Announcement read:", error);
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };

    let datetime = new Date(props.appearDatetime);

    return (
        <div className={className}>
            <p className="mx-2 mt-2 w-full text-xs font-bold uppercase text-gray-600">
                {datetime.toLocaleString("cs-CZ", {
                    weekday: "long",
                    hour: "2-digit",
                    minute: "2-digit",
                })}
            </p>
            {props.readBy ? (
                <p className="mx-2 text-xs uppercase text-gray-600">
                    Četl:{" "}
                    {(props.readBy.length ? props.readBy : ["Nikdo"]).join(
                        ", "
                    )}
                </p>
            ) : null}
            <div className="w-full md:flex">
                <div className="m-2 inline-block w-full md:w-auto md:flex-grow">
                    <CiviMarkdown>{props.content}</CiviMarkdown>
                </div>
                {!props.read && !user.is_org ? (
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
        </div>
    );
}

export function AnnouncementList(props: {
    announcements: any;
    deletable: boolean;
}) {
    return (
        <>
            {props.announcements.map((a: any) => (
                <Announcement key={a.id} deletable={props.deletable} {...a} />
            ))}
        </>
    );
}

function TeamStickers() {
    const { teamId } = useParams();
    const { team, error: teamError } = useTeam(teamId);
    const {
        data,
        error: dataError,
        mutate,
    } = useSWR<StickerT[]>(
        () => (teamId ? `game/teams/${teamId}/stickers` : null),
        fetcher
    );

    if (!team || !data) {
        return (
            <LoadingOrError
                error={teamError || dataError}
                message={"Nedaří se spojit serverem"}
            />
        );
    }

    return (
        <>
            <h1>Přehled samolepek pro tým {team.name}</h1>
            {data?.length == 0 ? (
                <p>Zatím nemáte žádné samolepky</p>
            ) : (
                <div className="flex w-full flex-wrap">
                    {data.map((s) => (
                        <Sticker key={s.id} sticker={s} mutate={mutate} />
                    ))}
                </div>
            )}
        </>
    );
}

function Sticker(props: { sticker: StickerT; mutate: () => void }) {
    const auth = useSelector((state: RootState) => state.auth);
    const { data: entities } = useEntities<any>();
    const [isUpdating, setIsUpdating] = useState(false);
    const [isPrinting, setIsPrinting] = useState(false);

    let awardedAt = new Date(props.sticker.awardedAt);

    let handleUpdate = () => {
        if (!props.sticker) return;
        setIsUpdating(true);
        axiosService
            .post<{}>(`/game/stickers/${props.sticker.id}/autoupdate/`)
            .then(() => {
                setIsUpdating(false);
                toast.success(`Samolepka ${props.sticker.id} aktualizována`);
                props.mutate();
            })
            .catch((error) => {
                console.error("Autoupdate sticker:", error);
                setIsUpdating(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };

    let imgUrl = `${process.env.REACT_APP_API_URL}/game/stickers/${props.sticker.id}/image`;
    return (
        <div className="m-2 flex flex flex-auto flex-col items-stretch rounded bg-white p-2 shadow">
            <div className="self-stretch">
                <a href={imgUrl}>
                    <img
                        src={imgUrl}
                        className="mx-auto"
                        style={{ maxWidth: "200px" }}
                    />
                </a>
            </div>
            <div className="w-full self-end">
                <div className="w-full text-center">
                    {entities && (
                        <>
                            {entities[props.sticker.entityId].name} varianta{" "}
                            {props.sticker.type}
                        </>
                    )}
                </div>
                <div className="w-full text-center text-sm text-gray-600">
                    Uděleno:{" "}
                    {awardedAt.toLocaleString("cs-CZ", {
                        weekday: "long",
                        hour: "2-digit",
                        minute: "2-digit",
                    })}
                </div>

                {auth.account?.user?.is_org && (
                    <div className="flex flex-wrap">
                        <Button
                            disabled={isUpdating}
                            onClick={handleUpdate}
                            label="Aktualizovat"
                            className="focus:shadow-outline m-2 flex-auto rounded bg-purple-500 py-2 px-4 font-bold text-white shadow hover:bg-purple-400 focus:outline-none"
                        />
                        <Button
                            disabled={isPrinting}
                            onClick={() => setIsPrinting(true)}
                            label="Vytisknout"
                            className="focus:shadow-outline m-2 flex-auto rounded bg-purple-500 py-2 px-4 text-center font-bold text-white shadow hover:bg-purple-400 focus:outline-none"
                        />
                    </div>
                )}
            </div>
            {isPrinting && (
                <Dialog onClose={() => setIsPrinting(false)}>
                    <PrintStickers
                        stickers={[props.sticker]}
                        onPrinted={() => setIsPrinting(false)}
                    />
                </Dialog>
            )}
        </div>
    );
}
