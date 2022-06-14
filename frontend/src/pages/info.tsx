import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { Dialog, LoadingOrError } from "../elements";
import { SuccessMessage } from "../elements/messages";
import { useCurrentTurn } from "../elements/turns";
import axiosService, { fetcher } from "../utils/axios";
import { AnnouncementList } from "./dashboard";
import { useScanner } from "./scanner";
import QRCode from "react-qr-code";
import { ActionMessage, useActionPreview } from "../elements/action";
import { toast } from "react-toastify";
import produce from "immer";
import { useTeam } from "../elements/team";
import useSWRImmutable from "swr/immutable";

export function InfoScreen() {
    return (
        <>
            <div className="flex min-h-screen flex-col bg-gray-100 font-sans leading-normal tracking-normal">
                <div className="mx-auto w-full flex-grow pt-1">
                    <div className="mb-16 w-full px-2 py-10 leading-normal text-gray-800 md:mt-2 md:px-0">
                        <InfoScreenContent />
                    </div>
                </div>

                <footer className="border-t border-gray-400 bg-white shadow">
                    <div className="container mx-auto flex max-w-md py-8"></div>
                </footer>
            </div>
        </>
    );
}

function InfoScreenContent() {
    return (
        <div className="text-center">
            <Countdown />
            <PublicAnnouncements />
            <AutoFeedDialog />
            <PlagueDialog />
        </div>
    );
}

function Countdown() {
    const { info, reload, error } = useCurrentTurn();
    const [elapsed, setElapsed] = useState<number>(0);

    useEffect(() => {
        let int = setInterval(() => {
            setElapsed(elapsed + 1);
        }, 1000);
        return () => clearInterval(int);
    }, [elapsed, setElapsed]);

    let now = new Date();

    if (!error && !info) {
        return (
            <LoadingOrError
                loading={!error && !info}
                error={error}
                message="Něco se nepovedlo"
            />
        );
    }

    let paused = info?.id == -1 || !info?.end || !info?.start;

    let minutesRem = 0;
    let secsRem = 0;
    let minutesFow = 0;
    let secsFow = 0;
    if (!paused) {
        // @ts-ignore
        let remainingSecs = (info.end.getTime() - now.getTime()) / 1000;
        if (remainingSecs <= 0) {
            // @ts-ignore
            reload();
            remainingSecs = 0;
        }
        minutesRem = Math.floor(remainingSecs / 60);
        secsRem = Math.floor(remainingSecs % 60);

        // @ts-ignore
        let forSecs = (now.getTime() - info.start.getTime()) / 1000;
        minutesFow = Math.floor(forSecs / 60);
        secsFow = Math.floor(forSecs % 60);
    }

    return (
        <>
            <h1 style={{ fontSize: "80px" }} className="mb-12 p-5">
                {paused
                    ? "Hra je aktuálně pozastavena"
                    : // @ts-ignore
                      `Herní čas ${info.id}­–${String(minutesFow).padStart(
                          2,
                          "0"
                      )}:${String(secsFow).padStart(2, "0")}`}
            </h1>
            <div style={{ fontSize: "300px" }} className="leading-none">
                {!paused &&
                    `${String(minutesRem).padStart(2, "0")}:${String(
                        secsRem
                    ).padStart(2, "0")}`}
            </div>
        </>
    );
}

function PublicAnnouncements() {
    const { data } = useSWR<any>("/announcements/public", fetcher, {
        refreshInterval: 20000,
    });

    if (!data || data.length == 0) return null;

    return (
        <div className="container mx-auto">
            <h1>Poslední veřejná oznámení:</h1>
            <div id="announcements" className="text-left">
                <AnnouncementList announcements={data} deletable={false} />
            </div>
        </div>
    );
}

function AutoFeedDialog() {
    const [teamId, setTeamId] = useState<string | undefined>(undefined);

    useScanner((items: string[]) => {
        if (items.length != 1) return;
        if (items[0].startsWith("krm-")) {
            let teamId = items[0].replace("krm-", "");
            setTeamId(teamId);
        }
    });

    if (!teamId) return null;

    return (
        <Dialog onClose={() => setTeamId(undefined)}>
            <AutoFeedDialogImpl
                teamId={teamId}
                onClose={() => setTeamId(undefined)}
            />
        </Dialog>
    );
}

function AutoFeedDialogImpl(props: { teamId: string; onClose: () => void }) {
    const actionArgs = useMemo(() => {
        return { team: props.teamId, materials: {} };
    }, [props.teamId]);
    const { preview, error } = useActionPreview("ActionFeed", actionArgs);
    const [submitting, setSubmitting] = useState(false);

    useScanner((items: string[]) => {
        if (items.length != 1) return;
        if (items[0] == "ans-no") {
            props.onClose();
        }
        if (items[0] == "ans-yes" && preview && preview.success) {
            setSubmitting(true);
            axiosService
                .post<any, any>("/game/actions/initiate/", {
                    action: "ActionFeed",
                    args: actionArgs,
                })
                .then((data) => {
                    toast.success("Akce provedena");
                })
                .catch((error) => {
                    setSubmitting(false);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                })
                .finally(() => {
                    setSubmitting(false);
                    props.onClose();
                });
        }
    });

    if (!preview)
        return (
            <LoadingOrError
                loading={!preview && !error}
                error={error}
                message="Něco se pokazilo. Řekni to Honzovi"
            />
        );

    return (
        <div className="text-left">
            <h1>Automatické krmení</h1>

            <ActionMessage response={preview} />
            {submitting ? (
                <div className="w-full py-14 text-center text-2xl">
                    Odesílám
                </div>
            ) : (
                <>
                    <h2>Přejete si pokračovat?</h2>
                    <div className="my-6 flex w-full">
                        <div className="mx-0 w-1/2 p-3 text-center">
                            {preview.success && (
                                <>
                                    <h1>ANO</h1>
                                    <QRCode
                                        value="ans-yes"
                                        className="mx-auto"
                                    />
                                </>
                            )}
                        </div>
                        <div className="mx-0 w-1/2 p-3 text-center">
                            <h1>NE</h1>
                            <QRCode value="ans-no" className="mx-auto" />
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function PlagueDialog() {
    const [teamId, setTeamId] = useState<string | undefined>(undefined);
    const [words, setWords] = useState<string[]>([]);

    useScanner((items: string[]) => {
        let wordsToAdd = [];
        for (const item of items) {
            if (item.startsWith("tym-")) {
                setTeamId(item);
                continue;
            }
            if (item.startsWith("mor-")) {
                wordsToAdd.push(item.replace("mor-", "").toUpperCase().trim());
                continue;
            }
            if (item.startsWith("tec-")) {
                wordsToAdd.push(item);
                continue;
            }
        }
        if (wordsToAdd.length > 0) setWords(words.concat(wordsToAdd));
    });

    let handleClose = () => {
        setWords([]);
        setTeamId(undefined);
    };

    console.log(teamId, words.length);
    if (!teamId && words.length == 0) return null;

    return (
        <Dialog onClose={handleClose}>
            <PlagueDialogImpl
                teamId={teamId}
                words={words}
                onClose={handleClose}
            />
        </Dialog>
    );
}

function PlagueDialogImpl(props: {
    teamId?: string;
    words: string[];
    onClose: () => void;
}) {
    const { team } = useTeam(props.teamId);
    const [submitting, setSubmitting] = useState(false);
    const [response, setResponse] = useState<any>(undefined);
    const { data: words, error } = useSWRImmutable<Record<string, string>>(
        "game/plague/",
        fetcher
    );

    useScanner((items: string[]) => {
        for (const item of items) {
            if (item === "ans-cancel") {
                props.onClose();
                return;
            }
            if (item === "ans-submit") {
                if (!props.teamId) {
                    toast.error("Nebyl zadán tým, nemůžu odeslat recept");
                    return;
                }
                axiosService
                    .post<any, any>("/game/actions/initiate/", {
                        action: "ActionPlagueSentence",
                        args: {
                            team: props.teamId,
                            words: props.words,
                        },
                    })
                    .then((data) => {
                        setSubmitting(false);
                        setResponse(data.data);
                    })
                    .catch((error) => {
                        setSubmitting(false);
                        toast.error(`Nastala neočekávaná chyba: ${error}`);
                    });
            }
        }
    });

    if (!words) {
        return (
            <LoadingOrError
                loading={!words && !error}
                error={error}
                message={"Něco se pokazilo, dej o tom vědět Honzovi"}
            />
        );
    }

    let valid = true;
    let mappedWords = props.words.map((w, i) => {
        if (w in words) return <span key={i}>{words[w]} </span>;
        valid = false;
        return (
            <span key={i} className="red-500 font-bold">
                Neznámé slovo{" "}
            </span>
        );
    });

    return (
        <>
            <div className="text-left">
                <h1>Zadávání receptu {team && <> pro tým {team.name}</>} </h1>
                <div className="text-2xl">Aktuální recept je: {mappedWords}</div>
            </div>

            {submitting ? (
                <div className="w-full py-14 text-center text-2xl">
                    Odesílám
                </div>
            ) : (
                !response &&
                <>
                    <div className="my-6 flex w-full">
                        <div className="mx-0 w-1/2 p-3 text-center">
                            <h1>Zadat větu</h1>
                            <QRCode value="ans-submit" className="mx-auto" />
                        </div>
                        <div className="mx-0 w-1/2 p-3 text-center">
                            <h1>Zrušit větu</h1>
                            <QRCode value="ans-cancel" className="mx-auto" />
                        </div>
                    </div>
                </>
            )}
            {response && (
                <div className="my-5">
                    <ActionMessage response={response} />
                    <h1>Zavřít</h1>
                    <QRCode value="ans-cancel" className="mx-auto" />
                </div>
            )}
        </>
    );
}
