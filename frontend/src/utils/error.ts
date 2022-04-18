export function combineErrors(errors: any[]) {
    return errors.reduce((result, current) => {
        return result ? result : current;
    }, undefined);
}
