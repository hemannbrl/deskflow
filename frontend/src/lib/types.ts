export type Role = "requester" | "agent" | "manager";

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
}
