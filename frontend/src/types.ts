
export interface AccountResponse {
  user: {
    id: string;
    username: string;
  };
  access: string;
  refresh: string;
}

export interface UserResponse {
  id: string;
  username: string;
}
