export type Decimal = string;

export type TurnId = number;

export interface User {
    id: string;
    username: string;
    is_org: boolean;
    is_superuser: boolean;
    team?: Team;
}

export interface Team extends EntityBase {
    color: string;
}

// Entities

export type EntityId = string;
export type TeamId = EntityId;

export type DieId = EntityId;
export type ResourceId = EntityId;
export type TileFeatureId = EntityId;
export type NaturalResourceId = TileFeatureId;
export type VyrobaId = EntityId;
export type BuildingId = TileFeatureId;
export type BuildingUpgradeId = TileFeatureId;
export type TeamAttributeId = EntityId;
export type TechId = EntityId;
export type MapTileEntityId = EntityId;

export interface EntityBase {
    id: EntityId;
    name: string;
    icon?: string;
}

export interface DieEntity extends EntityBase {
    briefName: string;
}

export interface ResourceEntity extends EntityBase {
    produces?: ResourceId;
}

export interface EntityWithCost extends EntityBase {
    cost: Record<ResourceId, Decimal>;
    points: number;
    unlockedBy: TechId[];
}

export interface VyrobaEntity extends EntityWithCost {
    reward: [ResourceId, Decimal];
    requiredTileFeatures: TileFeatureId[];
}

export interface BuildingEntity extends EntityWithCost {
    requiredTileFeatures: TileFeatureId[];
    upgrades: BuildingUpgradeId[];
}

export interface BuildingUpgradeEntity extends EntityWithCost {
    building: BuildingId;
}

export interface TeamAttributeEntity extends EntityWithCost {}

export interface TechEntity extends EntityWithCost {
    unlocks: EntityWithCost[];
}

export interface MapTileEntity extends EntityBase {
    index: number;
    naturalResources: NaturalResourceId[];
    richness: number;
}

// Team Entity Info

export interface TeamEntityResource extends ResourceEntity {
    available: number;
}

export interface TeamEntityVyroba extends VyrobaEntity {
    allowedTiles: string[];
}

export interface EntityTeamAttribute extends EntityWithCost {}

export interface TeamEntityTeamAttribute extends EntityTeamAttribute {
    owned: boolean;
}

export enum TechStatus {
    Owned = "owned",
    Researching = "researching",
    Available = "available",
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
    Game = "game",
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
    Fail = "fail",
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
    description?: string;
}

// AnyAction

export interface ServerArgTypeInfo {
    type: string;
    required: boolean;
    default?: any;
    subtypes?: ServerArgTypeInfo[];
    values?: Record<string, any>;
}

export interface ServerActionType {
    id: string;
    has_init: boolean;
    args: Record<string, ServerArgTypeInfo>;
}
