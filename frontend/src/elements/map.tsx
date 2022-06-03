import { classNames, LoadingOrError } from ".";
import { useEntities } from "./entities";

export function TileSelect(props: {
    value?: any;
    onChange: (tile: any) => void;
    className?: string;
}) {
    const { data: tiles, loading, error } = useEntities<any>("tiles");

    if (!tiles || error) {
        return (
            <LoadingOrError
                loading={loading}
                error={error}
                message="Nemůžu načíst dlaždice"
            />
        );
    }

    let className = classNames("select", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) => props.onChange(tiles[e.target.value])}
        >
            <option>Žádné políčko</option>
            {Object.values(tiles).map((t: any) => (
                <option key={t.id} value={t.id}>
                    {t.name}
                </option>
            ))}
        </select>
    );
}
