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
    Dialog,
    LoadingOrError,
    RequireOrg,
} from "../elements";
import { useTeam, useTeamIdFromUrl, useTeams } from "../elements/team";
import { RootState } from "../store";
import { Team, Sticker as StickerT } from "../types";
import {
    faUsers,
    faBriefcase,
    faCalendar,
    faCogs,
    faWarehouse,
    faWheatAwn,
    faQrcode,
} from "@fortawesome/free-solid-svg-icons";
import useSWR from "swr";
import axiosService, { fetcher } from "../utils/axios";
import { combineErrors } from "../utils/error";
import { EntityTag, useEntities, useTeamTechs } from "../elements/entities";
import { sortTechs } from "./techs";
import { useState } from "react";
import { toast } from "react-toastify";
import { TurnCountdownSticker } from "../elements/turns";
import QRCode from "react-qr-code";
import { strictEqual } from "assert";
import { PrintStickers, PrintVoucher } from "../elements/printing";

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
        { url: "vouchers", name: "Směnky", orgOnly: true },
    ];

    let accessibleSubLinks = user?.isOrg
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
            {user?.isOrg ? <MiddleTeamMenu teams={teams} /> : null}
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
    const user = useSelector((state: RootState) => state.auth.account?.user);
    const { teams, error: teamError } = useTeams();
    const [urlTeamId] = useTeamIdFromUrl();

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
        <>
            <TurnCountdownSticker />
            <Routes>
                <Route
                    path=""
                    element={
                        user?.isOrg ? (
                            <Navigate
                                to={`${urlTeamId || firstTeam.id}/#team=${
                                    urlTeamId || firstTeam.id
                                }`}
                            />
                        ) : (
                            <Navigate to={`${user?.team.id}`} />
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
                <Route
                    path=":teamId/vouchers"
                    element={
                        <RequireOrg>
                            <TeamVouchers />
                        </RequireOrg>
                    }
                />
                <Route path="*" element={<Navigate to="" />} />
            </Routes>
        </>
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
                    {data.worldTurn == 0
                        ? "Hra ještě nezačala."
                        : `Hra se nachází v ${data.worldTurn}. kole, vy se nachzíte ${data.teamTurn}. kole`}
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
            <div className="section w-full">
                <h2 className="text-xl" id="section-1">
                    Různé
                </h2>

                <div className="flex w-full flex-wrap">
                    <Card label="Krmení" color={team.color} icon={faQrcode}>
                        <QRCode
                            value={`krm-${team.id}`}
                            size={128}
                            className="m-10 mx-auto max-h-40"
                        />
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
    const { team, error: teamError, loading: teamLoading } = useTeam(teamId);
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
                loading={teamLoading || (!data && !dataError)}
                error={combineErrors([teamError, dataError])}
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
            .post<any, any>(`/game/stickers/${props.sticker.id}/upgrade/`)
            .then((data) => {
                setIsUpdating(false);
                toast.success(`Samolepka ${props.sticker.id} aktualizována`);
                props.mutate();
            })
            .catch((error) => {
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

                {auth.account?.user?.isOrg && (
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

function TeamVouchers() {
    const { teamId } = useParams();
    const { team, error: teamError, loading: teamLoading } = useTeam(teamId);
    const { data, error: dataError } = useSWR<any[]>(
        () => (teamId ? `game/teams/${teamId}/vouchers` : null),
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
            <h1>Seznam směnek pro tým {team.name}</h1>
            <div className="w-full">
                {data.map((v) => (
                    <Voucher key={v.id} voucher={v} />
                ))}
            </div>
        </>
    );
}

function Voucher(props: { voucher: any }) {
    const [printing, setIsPrinting] = useState(false);

    let v = props.voucher;

    let className = classNames(
        "w-full rounded bg-white p-5 shadow my-3",
        v.withdrawn && "bg-gray-200",
        v.performed && !v.withdrawn && "bg-green-200"
    );

    return (
        <div className={className}>
            <h1>Odložený efekt {props.voucher.slug}</h1>
            <div className="flex w-full p-0">
                <div className="m-0 w-full md:w-2/3">
                    <ul>
                        <li>
                            <b>Popis: </b>
                            {v?.description
                                ? v.description
                                : "Popisek nebyl implementován. Honza a Maara, uličníci jedni!"}
                        </li>
                        <li>
                            <b>Vyplní se v: </b>
                            {v.round}. kole, {Math.round(v.target / 60)}. minutě
                        </li>
                        <li>
                            <b>Stav:</b>{" "}
                            {v.performed
                                ? v.withdrawn
                                    ? "Vybráno"
                                    : "Nevybráno"
                                : "Čeká na vyplnění"}
                        </li>
                    </ul>
                </div>
                <div className="m-0 w-full md:w-1/3">
                    <Button
                        label={printing ? "Tisknu" : "Tisknout"}
                        onClick={() => setIsPrinting(true)}
                    />
                </div>
            </div>

            {printing && (
                <Dialog onClose={() => setIsPrinting(false)}>
                    <PrintVoucher
                        voucher={props.voucher.slug}
                        onPrinted={() => setIsPrinting(false)}
                    />
                </Dialog>
            )}
        </div>
    );
}
