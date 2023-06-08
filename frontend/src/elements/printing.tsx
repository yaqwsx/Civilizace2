import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import useSWR from "swr";
import { useLocalStorage } from "usehooks-ts";
import { Button, FormRow, LoadingOrError } from ".";
import { Printer, Sticker } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { EntityTag } from "./entities";
import { useTeams } from "./team";

export function usePrinters() {
    const { data: printers, error } = useSWR<Printer[]>(
        "/game/printers/",
        fetcher,
        {
            revalidateOnMount: true,
            refreshInterval: 10000,
        }
    );
    return {
        printers,
        error,
    };
}

function PrinterSelect(props: {
    printers: Printer[];
    value?: Printer;
    onChange: (p: Printer | undefined) => void;
}) {
    let handleChange = (name: string) => {
        props.onChange(props.printers.find((x) => x.name == name));
    };
    return (
        <select
            className="select"
            value={props.value?.name}
            onChange={(e) => handleChange(e.target.value)}
        >
            <option value="">—— Nic nevybráno ——</option>
            {props.printers.map((p) => (
                <option key={p.name} value={p.name}>
                    {p.name} ({p.printsStickers ? "SAMOLEPKA" : "PAPÍR"})
                </option>
            ))}
        </select>
    );
}

export function PrintStickers(props: {
    stickers: Sticker[];
    onPrinted: () => void;
}) {
    const { teams, error: teamsError } = useTeams();
    const { printers, error } = usePrinters();
    const [stickerPrinter, setStickerPrinter] = useLocalStorage<
        string | undefined
    >("stickerPrinter", undefined);
    const [paperPrinter, setPaperPrinter] = useLocalStorage<string | undefined>(
        "paperPrinter",
        undefined
    );
    const [isPrinting, setIsPrinting] = useState(false);

    useEffect(() => {
        if (!printers) {
            return;
        }
        let ids = printers.map((x) => x.name);
        if (paperPrinter && !ids.includes(paperPrinter))
            setPaperPrinter(undefined);
        if (stickerPrinter && !ids.includes(stickerPrinter))
            setStickerPrinter(undefined);
    }, [paperPrinter, stickerPrinter]);

    if (!printers || !teams) {
        return (
            <LoadingOrError
                error={error || teamsError}
                message="Něco se nepovedlo. Zkouším znovu"
            />
        );
    }

    let paperPrinterObj = printers.find((x) => x.name == paperPrinter);
    let stickerPrinterObj = printers.find((x) => x.name == stickerPrinter);

    const handlePrint = () => {
        setIsPrinting(true);
        Promise.all(
            props.stickers.map(async (sticker) => {
                return axiosService
                    .post<{}>(`/game/stickers/${sticker.id}/print/`, {
                        printerId:
                            sticker.entityId.startsWith("tec-") ||
                            sticker.entityId.startsWith("bui-") ||
                            sticker.entityId.startsWith("vyr")
                                ? stickerPrinterObj?.id
                                : paperPrinterObj?.id,
                    })
                    .then(() => {
                        toast.success(`Samolepka ${sticker.id} vytištěna`);
                    })
                    .catch((error) => {
                        console.error(error);
                        toast.error(
                            `Samolepka ${sticker.id}: neočekávaná chyba: ${error}`
                        );
                    });
            })
        ).finally(() => {
            setIsPrinting(false);
            props.onPrinted();
        });
    };

    return (
        <div className="my-6 w-full">
            <h1>Tisknout samolepky:</h1>
            <FormRow label="Samolepky k vytištění">
                <ul>
                    {props.stickers.map((s) => (
                        <li key={s.id} className="list-disc">
                            <EntityTag id={s.entityId} /> typ {s.type} pro{" "}
                            {teams.find((x) => x.id === s.team)?.name}
                        </li>
                    ))}
                </ul>
            </FormRow>
            <FormRow
                label="Tiskárna na papír"
                error={paperPrinter ? null : "Musí být vybráno"}
            >
                <PrinterSelect
                    printers={printers}
                    value={paperPrinterObj}
                    onChange={(p) => setPaperPrinter(p?.name)}
                />
            </FormRow>
            <FormRow
                label="Tiskárna na samolepky"
                error={stickerPrinter ? null : "Musí být vybráno"}
            >
                <PrinterSelect
                    printers={printers}
                    value={stickerPrinterObj}
                    onChange={(p) => setStickerPrinter(p?.name)}
                />
            </FormRow>
            <Button
                label={isPrinting ? "Tisknu, prosím počkejte" : "Tisknout"}
                disabled={isPrinting || !paperPrinter || !stickerPrinter}
                className="w-full"
                onClick={handlePrint}
            />
        </div>
    );
}
