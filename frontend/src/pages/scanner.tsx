import _ from "lodash";
import onScan from "onscan.js";
import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useState,
} from "react";
import { useNavigate } from "react-router-dom";

function decodeKeyEvent(event: KeyboardEvent) {
    if (event.code === "Space") return " ";
    if (event.code.startsWith("Digit"))
        return event.code.charAt(event.code.length - 1);
    if (event.code === "Minus" || event.code === "Slash") return "-";
    return onScan.decodeKeyEvent(event);
}

interface ScannerContextType {
    items: string[];
}

export const ScannerContext = createContext<ScannerContextType>({
    items: [],
});

export function ScannerDispatcher(props: JSX.ElementChildrenAttribute) {
    const [items, setItems] = useState<string[]>([]);

    const handleCodes = (code: string) => {
        console.log("Scanned:", code);
        const items = code.split(" ").map((x) => x.trim());
        setItems(items);
    };

    useEffect(() => {
        onScan.attachTo(document, {
            onScan: handleCodes,
            keyCodeMapper: decodeKeyEvent,
        });
        // @ts-ignore
        window.simscan = (text: string) => {
            onScan.simulate(document, text);
        };
        return () => {
            onScan.detachFrom(document);
        };
    }, [handleCodes]);

    return (
        <ScannerContext.Provider
            value={{
                items,
            }}
        >
            {props.children}
        </ScannerContext.Provider>
    );
}

export function useScanner(callback: (words: string[]) => void) {
    const { items } = useContext(ScannerContext);

    useEffect(() => {
        callback(items);
    }, [items]);
}
