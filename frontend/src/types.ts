export interface Team {
    id: string;
    name: string;
    color: string;
}

type ResourceId = string;
type DieId = string;
type TechId = string;

export interface EntityBase {
    id: string;
    name: string;
}

export interface ResourceType {
    level: number;
    name: string;
    prodName: string;
}

export interface EntityResource extends EntityBase {
    typ?: ResourceType;
    produces?: ResourceId;
}

export interface TeamEntityResource extends EntityResource {
    availabe: number
}

export interface EntityVyroba extends EntityBase {
    cost: Record<ResourceId, number>;
    die: [DieId, number];
    reward: [ResourceId, number];
    techs: TechId[];
}

export type Entity =
    | EntityResource
    | EntityVyroba;

export interface AccountResponse {
    user: {
        id: string;
        username: string;
        isOrg: boolean;
        team: Team;
    };
    access: string;
    refresh: string;
}

export interface UserResponse {
    id: string;
    username: string;
}
