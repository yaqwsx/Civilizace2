import { EntityId } from "@reduxjs/toolkit";

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
    points: number;
    unlockedBy: [EntityId, DieId][];
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
    Important = "important"
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

export interface Round {
    seq: number;
    start: Date;
    editable: boolean;
    length: number;
}

export interface RoundSentinel {
    seq: number;
}

export enum ActionStatus {
    Success = "success",
    Fail = "fail"
}


export interface ActionResponse {
    success: boolean;
    message: string;
    action?: Number;
}

export interface ActionCommitResponse {
    dotsRequired: Number;
    allowedDice: string[];
}
