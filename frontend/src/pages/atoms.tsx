import { atom, useAtom } from 'jotai'
import { atomWithHash } from "jotai/utils"
import { useEffect } from 'react';

export const entityAtom = atomWithHash<string | null>("team", null);

export const menuShownAtom = atomWithHash<boolean>("menu", false);

export function useHideMenu() {
    const [menuShown, setMenuShown] = useAtom(menuShownAtom);
    useEffect(() => {setMenuShown(false);}, [])
}
