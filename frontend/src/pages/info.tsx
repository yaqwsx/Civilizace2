import { useEffect, useState } from "react";
import useSWR from "swr";
import { Dialog, LoadingOrError } from "../elements";
import { SuccessMessage } from "../elements/messages";
import { useCurrentTurn } from "../elements/turns";
import { fetcher } from "../utils/axios";
import { AnnouncementList } from "./dashboard";
import { useScanner } from "./scanner";
import QRCode from "react-qr-code";

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

    let paused = info?.id == -1 || !info?.end;

    let minutes = 0;
    let secs = 0;
    if (!paused) {
        // @ts-ignore
        let remainingSecs = (info.end.getTime() - now.getTime()) / 1000;
        if (remainingSecs <= 0) {
            // @ts-ignore
            reload();
            remainingSecs = 0;
        }
        minutes = Math.floor(remainingSecs / 60);
        secs = Math.floor(remainingSecs % 60);
    }

    return (
        <>
            <h1 style={{ fontSize: "80px" }} className="mb-12 p-5">
                {paused
                    ? "Hra je aktuálně pozastavena"
                    : // @ts-ignore
                      `Probíhá ${info.id}. kolo`}
            </h1>
            <div style={{ fontSize: "300px" }} className="leading-none">
                {!paused &&
                    `${String(minutes).padStart(2, "0")}:${String(
                        secs
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
        if (items[0].startsWith("ans-")) {
            setTeamId(undefined);
        }
        if (items[0].startsWith("krm-")) {
            let teamId = items[0].replace("krm-", "");
            setTeamId(teamId);
        }
    });

    if (!teamId) return null;

    return (
        <Dialog onClose={() => setTeamId(undefined)}>
            <div className="text-left">
                <h1>Automatické krmení</h1>

                <SuccessMessage>
                    <h1>Tady bude náhled krmení...</h1>
                </SuccessMessage>
                <h2>Přejete si pokračovat?</h2>
                <div className="w-full flex my-6">
                    <div className="mx-0 w-1/2 p-3 text-center">
                        <h1>ANO</h1>
                        <QRCode value="ans-yes" className="mx-auto" />
                    </div>
                    <div className="mx-0 w-1/2 p-3 text-center">
                        <h1>NE</h1>
                        <QRCode value="ans-no" className="mx-auto" />
                    </div>
                </div>
            </div>
        </Dialog>
    );
}