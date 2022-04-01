export interface TeamResponse {
  id: string;
  name: string;
  color: string;
}

export interface AccountResponse {
  user: {
    id: string;
    username: string;
    isOrg: boolean;
    team: TeamResponse;
  };
  access: string;
  refresh: string;
}

export interface UserResponse {
  id: string;
  username: string;
}
