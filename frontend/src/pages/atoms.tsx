import { atom } from 'jotai'
import { atomWithHash } from "jotai/utils"

export const entityAtom = atomWithHash<string | null>("team", null);
