import _ from "lodash";
import { useEffect, useState } from "react";
import QRCode from "react-qr-code";
import { toast } from "react-toastify";
import useSWR from "swr";
import { Dialog, LoadingOrError } from "../elements";
import { ActionMessage, useActionPreview } from "../elements/action";
import { useScanner } from "../elements/scanner";
import { useCurrentTurn } from "../elements/turns";
import { ActionResponse, TeamAnnouncement } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { AnnouncementList } from "./dashboard";

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
        </div>
    );
}

function Countdown() {
    const { info, mutate: reload, error } = useCurrentTurn();
    const [elapsed, setElapsed] = useState(0);

    useEffect(() => {
        let int = setInterval(() => {
            setElapsed(elapsed + 1);
        }, 1000);
        return () => clearInterval(int);
    }, [elapsed, setElapsed]);

    let now = new Date();

    if (!info) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
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
                      `Herní čas: ${info.id}­–${String(minutesFow).padStart(
                          2,
                          "0"
                      )}:${String(secsFow).padStart(2, "0")}`}
            </h1>
            <div style={{ fontSize: "30px" }} className="leading-none">
                {!paused && `Čas do konce kola:`}
            </div>
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
    const { data } = useSWR<TeamAnnouncement[]>(
        "/announcements/public",
        fetcher,
        {
            refreshInterval: 20000,
        }
    );

    if (_.isNil(data) || data.length === 0) {
        return null;
    }

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
    const [teamId, setTeamId] = useState<string>();

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
    const { previewResponse, error } = useActionPreview({
        actionId: "FeedAction",
        actionArgs: { team: props.teamId },
        argsValid: () => true,
    });
    const [submitting, setSubmitting] = useState(false);

    useScanner((items: string[]) => {
        if (items.length != 1) return;
        if (items[0] == "ans-no") {
            props.onClose();
        }
        if (items[0] == "ans-yes" && previewResponse?.success) {
            setSubmitting(true);
            axiosService
                .post<ActionResponse>("/game/actions/team/initiate/", {
                    action: "FeedAction",
                    args: { team: props.teamId },
                })
                .then((data) => {
                    toast.success("Akce provedena");
                })
                .catch((error) => {
                    console.error("Initiate feeding:", error);
                    setSubmitting(false);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                })
                .finally(() => {
                    setSubmitting(false);
                    props.onClose();
                });
        }
    });

    if (!previewResponse)
        return (
            <LoadingOrError
                error={error}
                message="Něco se pokazilo. Řekni to Honzovi"
            />
        );

    return (
        <div className="text-left">
            <h1>Automatické krmení</h1>

            <ActionMessage response={previewResponse} />
            {submitting ? (
                <div className="w-full py-14 text-center text-2xl">
                    Odesílám
                </div>
            ) : (
                <>
                    <h2>Přejete si pokračovat?</h2>
                    <div className="my-6 flex w-full">
                        <div className="mx-0 w-1/2 p-3 text-center">
                            {previewResponse.success && (
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
