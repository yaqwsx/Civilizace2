import { useEffect, useState } from "react";
import { useDeepCompareEffectNoCheck } from "use-deep-compare-effect";

export function useDebounceDeep<T>(value: T, delay?: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useDeepCompareEffectNoCheck(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay || 500);

        return () => {
            clearTimeout(timer);
        };
    }, [value, delay]);
    return debouncedValue;
}
