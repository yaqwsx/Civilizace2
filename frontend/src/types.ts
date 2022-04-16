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

export interface EntityWithCost extends EntityBase {
    cost: Record<ResourceId, number>;
    points: number;
}

export interface EntityVyroba extends EntityWithCost {
    reward: [ResourceId, number];
    techs: TechId[];
}

export enum TechStatus {
    Owned = "owned",
    Researching = "researching",
    Available = "available"
}

export interface Task {
    id: string;
    name: string;
    teamDescription: string;
    orgDescription?: string; // Available only for orgs
}

export interface EntityTech extends EntityWithCost {
    edges: Record<TechId, DieId>;
}

export interface TeamEntityTech extends EntityTech {
    status: TechStatus;
    assignedTask?: Task;
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
