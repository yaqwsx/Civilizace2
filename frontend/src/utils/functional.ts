export function objectMap(object: Record<string, any>, mapFn: (v: any) => any) {
    return Object.keys(object).reduce(function (
        result: Record<string, any>,
        key: string
    ) {
        result[key] = mapFn(object[key]);
        return result;
    },
    {});
}
