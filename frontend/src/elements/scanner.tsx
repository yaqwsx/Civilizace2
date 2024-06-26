import { useNavigate } from "react-router-dom";
import { MapActionType } from "../pages/map";

import onScan from "onscan.js";
import { createContext, useContext, useEffect, useState } from "react";
import { stringAtomWithHash } from "../utils/atoms";
import _ from "lodash";

export const urlReaderEntityAtom = stringAtomWithHash("entity");

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

export function getNavigatePage(items: string[]) {
    let page: string | undefined;
    const args: string[] = [];

    const setPage = (value: string) => {
        if (!_.isNil(page)) {
            console.warn("Multiple main pages from page navigation");
        }
        page = value;
    };

    items.forEach((item) => {
        if (item.startsWith("tym-")) {
            args.push(`team=${item}`);
        } else if (item.startsWith("vyr-")) {
            args.push(`entity=${item}`);
            args.push("vyrobaAction=vyroba");
            setPage("vyrobas");
        } else if (item.startsWith("tec-")) {
            args.push(`entity=${item}`);
            setPage("techs");
        } else if (item.startsWith("bui-")) {
            args.push(`entity=${item}`);
            args.push(`mapAction=${MapActionType.building}`);
            setPage("map");
        } else if (item.startsWith("bup-")) {
            args.push(`entity=${item}`);
            args.push(`mapAction=${MapActionType.buildingUpgrade}`);
            setPage("map");
        } else if (item.startsWith("att-")) {
            args.push(`entity=${item}`);
            args.push(`mapAction=${MapActionType.addAttribute}`);
            setPage("map");
        } else if (
            item.startsWith("res-") ||
            item.startsWith("mat-") ||
            item.startsWith("pro-") ||
            item.startsWith("mge-") ||
            item.startsWith("pge-")
        ) {
            args.push(`entity=${item}`);
            args.push(`mapAction=${MapActionType.setResource}`);
            args.push("tradable=true");
            setPage("map");
        }
    });
    return { page, args };
}

export function ScannerNavigator() {
    const navigate = useNavigate();

    useScanner((items: string[]) => {
        console.log("Scanner navigator:", items);
        const { page, args } = getNavigatePage(items);

        if (page) {
            console.log(`Navigating to ${page}#${args.join("&")}`);
            navigate(page);
            window.location.hash = `#${args.join("&")}`;
        }
    });
    return null;
}
