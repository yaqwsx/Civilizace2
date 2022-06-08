import { result } from "lodash";
import { useCallback, useContext, useEffect, useState } from "react";
import { toast } from "react-toastify";
import useSWR from "swr";
import {
    Button,
    CiviMarkdown,
    Dialog,
    FormRow,
    LoadingOrError,
} from "../elements";
import { EntityTag } from "../elements/entities";
import { ErrorMessage, SuccessMessage } from "../elements/messages";
import { PrintStickers } from "../elements/printing";
import axiosService, { fetcher } from "../utils/axios";
import { ScannerContext, useScanner } from "./scanner";

export function VouchersMenu() {
    return null;
}

export function Vouchers() {
    const [currentCode, setCurrentCode] = useState("");
    const [vouchers, setVouchers] = useState<string[]>([]);
    const [isSubmitting, setSubmitting] = useState(false);
    const [result, setResult] = useState<any>(null);

    useScanner((items: string[]) => {
        if (items.length != 1) return;
        if (!items[0].startsWith("vou-")) return;
        let code = items[0].replace("vou-", "").toUpperCase();
        if (vouchers.includes(code)) return;
        setVouchers(vouchers.concat([code]));
    });

    let handleAddVoucher = () => {
        let code = currentCode.toUpperCase().trim();
        if (code.length == 0) return;
        if (vouchers.includes(code)) return;
        setVouchers(vouchers.concat([code]));
        setCurrentCode("");
    };

    let handleRemoveVoucher = (code: string) => {
        setVouchers(vouchers.filter((x) => x != code));
    };

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<any, any>("/game/vouchers/withdraw/", {
                keys: vouchers,
            })
            .then((data) => {
                setSubmitting(false);
                setVouchers([]);
                setResult(data.data);
            })
            .catch((error) => {
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };
    console.log(result);
    return (
        <>
            <h1>Výběr směnek</h1>
            <FormRow label="Zadejte kód směnky:">
                <input
                    type="text"
                    value={currentCode}
                    onChange={(e) => setCurrentCode(e.target.value)}
                    onKeyDown={(event: any) => {
                        if (event.key === "Enter") {
                            handleAddVoucher();
                        }
                    }}
                />
            </FormRow>
            <Button
                label="Zadat směnku"
                className="w-full"
                onClick={handleAddVoucher}
                disabled={currentCode.trim().length == 0}
            />

            {vouchers.map((x) => (
                <Voucher
                    key={x}
                    code={x}
                    onDelete={() => handleRemoveVoucher(x)}
                />
            ))}

            <Button
                label={
                    isSubmitting ? "Výbírám směnky, počkejte" : "Vybrat směnky"
                }
                className="my-4 w-full bg-green-500 hover:bg-green-600"
                disabled={vouchers?.length == 0}
                onClick={handleSubmit}
            />

            {result && (
                <Dialog onClose={() => setResult(null)}>
                    <SuccessMessage><CiviMarkdown>{result.messages}</CiviMarkdown></SuccessMessage>
                    {result.stickers.toString()}
                    {result?.stickers?.length > 0 && (
                        <PrintStickers
                            stickers={result.stickers}
                            onPrinted={() => setResult(null)}
                        />
                    )}
                    <Button
                        className="my-6 w-full"
                        label="Budiž"
                        onClick={() => setResult(null)}
                    />
                </Dialog>
            )}
        </>
    );
}

function Voucher(props: { code: string; onDelete: () => void }) {
    const { data, error } = useSWR<any>(
        `/game/vouchers/${props.code}`,
        fetcher
    );

    return (
        <div className="my-4 mx-2 w-full rounded bg-white p-4">
            <h2 className="align-center">
                Směnka {props.code}{" "}
                <Button
                    className="align-center float-right inline-block bg-red-500 text-xs hover:bg-red-600"
                    label="Smazat"
                    onClick={props.onDelete}
                />
            </h2>

            <VoucherBody data={data} error={error} />
        </div>
    );
}

function VoucherBody(props: { data: any; error: any }) {
    let error = props.error;
    let data = props.data;

    if (error && error?.response?.status == 404) {
        return <ErrorMessage>Taková směnka neexistuje</ErrorMessage>;
    }

    if (!data) {
        return (
            <LoadingOrError
                loading={!data && !error}
                error={error}
                message="Nastala neočekávaná chyba"
            />
        );
    }

    if (data.withdrawn) {
        return (
            <ErrorMessage>
                Směnka už byla vybrána. Bude při výběru ignorována
            </ErrorMessage>
        );
    }

    if (!data.performed) {
        return (
            <ErrorMessage>
                Směnka ještě není platná. Bude platná v kole {data.round} a{" "}
                {Math.round(data.target / 60)} minut.
            </ErrorMessage>
        );
    }

    return (
        <SuccessMessage>
            Směnka je platná. Jedná se o odložený výsledek akce{" "}
            {String(data?.description)}
            {data?.stickers?.length > 0 && (
                <>
                    <h4>Tým také dostane následující samolepky:</h4>
                    <ul>
                        {data.stickers.map((s: string) => (
                            <li key={s} className="list-disc">
                                Samolepka <EntityTag id={s} />
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </SuccessMessage>
    );
}
