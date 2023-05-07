type EntityId = string;

export interface Team {
    id: string;
    name: string;
    color: string;
}

export interface User {
    id: string;
    username: string;
    isOrg: boolean;
    team: Team;
    is_superuser: boolean;
}

type ResourceId = string;
type DieId = string;
type TechId = string;

export interface EntityBase {
    id: string;
    name: string;
}

export interface ResourceType {
    id: string;
    level: number;
    name: string;
    prodName: string;
}

export interface EntityResource extends EntityBase {
    typ?: ResourceType;
    produces?: ResourceId;
}

export interface TeamEntityResource extends EntityResource {
    available: number
}

export interface EntityWithCost extends EntityBase {
    cost: Record<ResourceId, number>;
    points: number;
}

export interface EntityVyroba extends EntityWithCost {
    reward: [ResourceId, number];
    points: number;
    unlockedBy: [EntityId, DieId][];
}

export interface TeamEntityVyroba extends EntityVyroba {
    allowedTiles: string[]
}

export enum TechStatus {
    Owned = "owned",
    Researching = "researching",
    Available = "available"
}

export interface TaskAssignment {
    team: string;
    techId: string;
    assignedAt: Date;
    finishedAt?: Date;
}

export interface Task {
    id: string;
    name: string;
    teamDescription: string;
    orgDescription?: string; // Available only for orgs
    capacity: number;
    occupiedCount: number;
    assignments: TaskAssignment[];
    techs: TechId[];
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
    user: User;
    access: string;
    refresh: string;
}

export interface UserResponse {
    id: string;
    username: string;
}

export enum AnnouncementType {
    Normal = "normal",
    Important = "important",
    Game = "game"
}

export interface Announcement {
    id: number;
    author?: User;
    type: AnnouncementType;
    content: string;
    appearDatetime: Date;
    teams: string[];
    read?: string[];
}

export interface Turn {
    id: number;
    startedAt?: Date;
    shouldStartAt?: Date;
    enabled: boolean;
    duration: number;
    prev?: Turn;
    next?: Turn;
}

export interface Sticker {
    id: number;
    entityId: string;
    entityRevision: number;
    type: number;
    awardedAt: string;
    team: string;
}


export enum ActionStatus {
    Success = "success",
    Fail = "fail"
}

export interface ActionResponse {
    success: boolean;
    expected: boolean;
    message: string;
    action?: Number;
    stickers: Sticker[];
}

export interface ActionCommitResponse {
    requiredDots: number;
    allowedDice: EntityBase[];
    throwCost: number;
    description: string;
    team: string;
}

export interface Printer {
    id: number;
    name: string;
    address: string;
    port: number;
    registeredAt: string;
    printsStickers: boolean;
}

export interface UnfinishedAction {
    id: number;
    description?: string
}
