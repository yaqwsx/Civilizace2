import { SetStateAction, WritableAtom, atom, useAtom } from "jotai";
import { RESET, atomWithHash, atomWithReset } from "jotai/utils";

export function stringAtomWithHash(
    key: string,
    options?: {
        delayInit?: boolean;
        replaceState?: boolean;
        subscribe?: (callback: () => void) => () => void;
    }
): WritableAtom<string | null, SetStateAction<string | null> | typeof RESET> {
    return atomWithHash<string | null>(key, null, {
        serialize: (value: string | null) => value ?? "",
        deserialize: (value: string) => value || null,
        ...options,
    });
}
