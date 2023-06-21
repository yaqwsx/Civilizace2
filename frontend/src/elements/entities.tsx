import _ from "lodash";
import useSWRImmutable from "swr/immutable";
import { Decimal, EntityBase, EntityId } from "../types";
import { fetcher } from "../utils/axios";

export function useEntities<T = EntityBase>(entityType?: string) {
    return useSWRImmutable<Record<EntityId, T & EntityBase>>(
        () => (entityType ? `game/entities/${entityType}` : "game/entities"),
        fetcher
    );
}

export function EntityTag(props: { id: string; quantity?: Decimal }) {
    const { data } = useEntities();

    const entity = !_.isNil(data) ? data[props.id] : undefined;
    const isProduction =
        String(props.id).startsWith("pro-") ||
        String(props.id).startsWith("pge-");
    const nameClassNames = isProduction ? "underline" : "";

    const iconMarkup = entity?.icon ? (
        <>
            <img
                className="mx-1 inline-block h-8 w-8 align-middle"
                src={`/assets/icons/${entity.icon}`}
            />{" "}
        </>
    ) : null;

    return (
        <span>
            {!_.isNil(props.quantity) ? `${props.quantity}× ` : null}
            {iconMarkup}
            <span className={nameClassNames}>{entity?.name || props.id}</span>
        </span>
    );
}
