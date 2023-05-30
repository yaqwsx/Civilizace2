import { atom, useAtom } from 'jotai'
import { RESET, atomWithHash } from "jotai/utils"
import { useEffect } from 'react';

export const menuShownAtom = atomWithHash<boolean>("menu", false);

export function useHideMenu() {
    const [ , setMenuShown] = useAtom(menuShownAtom);
    useEffect(() => {setMenuShown(RESET);}, [])
}
