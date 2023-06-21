export function objectMap<T = any, R = T>(
    object: Record<string, T>,
    mapFn: (v: T) => R
) {
    return Object.entries(object).reduce<Record<string, R>>(
        (result, [key, value]) => {
            result[key] = mapFn(value);
            return result;
        },
        {}
    );
}
