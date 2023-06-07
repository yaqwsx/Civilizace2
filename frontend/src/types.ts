export type Decimal = string | number;

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

export interface ResourceTeamEntity extends ResourceEntity {
    available: Decimal;
}

export interface VyrobaTeamEntity extends VyrobaEntity {
    allowedTiles: string[];
}

export interface BuildingTeamEntity extends BuildingEntity {}
export interface BuildingUpgradeTeamEntity extends BuildingUpgradeEntity {}

export interface TeamAttributeTeamEntity extends TeamAttributeEntity {
    owned: boolean;
}

export enum TechStatus {
    Owned = "owned",
    Researching = "researching",
    Available = "available",
}

export interface TaskAssignment {
    team: TeamId;
    techId: TechId;
    assignedAt: Date;
    finishedAt?: Date;
}

export interface TeamTask {
    id: string;
    name: string;
    teamDescription: string;
    assignments: TaskAssignment[];
}

export interface Task extends TeamTask {
    orgDescription: string;
    capacity: number;
    occupiedCount: number;
    techs: TechId[];
}

export interface TechTeamEntity extends TechEntity {
    status: TechStatus;
    assignedTask?: TeamTask;
}

export interface TechOrgTeamEntity extends TechTeamEntity {
    status: TechStatus;
    assignedTask?: Task;
}

// Announcement

export enum AnnouncementType {
    Normal = "normal",
    Important = "important",
    Game = "game",
}

export interface TeamAnnouncement {
    id: number;
    type: AnnouncementType;
    content: string;
    read: boolean;
    appearDatetime: Date;
    readBy?: string[];
}

export interface Announcement {
    id: number;
    author?: string;
    appearDatetime: Date;
    type: AnnouncementType;
    content: string;
    teams: TeamId[];
    read?: TeamId[];
}

// Army

export enum ArmyMode {
    Idle = "Idle",
    Marching = "Marching",
    Occupying = "Occupying",
}
export enum ArmyGoal {
    Occupy = "Occupy",
    Eliminate = "Eliminate",
    Supply = "Supply",
    Replace = "Replace",
}

export interface Army {
    index: number;
    team: EntityId;
    name: string;
    level: number;
    equipment: number;
    boost: number;
    tile: EntityId | null;
    mode: ArmyMode;
    goal: ArmyGoal | null;
    reachableTiles?: EntityId[] | null;
}

// Dashboard

export interface TeamDashboard {
    population: { nospec: Decimal; all: Decimal };
    work: Decimal;
    culture: Decimal;
    withdraw_capacity: Decimal;
    worldTurn: TurnId;
    teamTurn: TurnId;
    researchingTechs: TechEntity[];
    productions: [EntityId, Decimal][];
    storage: [EntityId, Decimal][];
    granary: [EntityId, number][];
    feeding: {
        casteCount: number;
        tokensPerCaste: number;
        tokensRequired: number;
    };
    announcements: TeamAnnouncement[];
    armies: Army[];
    techs?: EntityId[];
    attributes?: EntityId[];
}

// Action

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

// Other

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

// Auth

export interface AccountResponse {
    user: User;
    access: string;
    refresh: string;
}

export interface UserResponse {
    id: string;
    username: string;
}
