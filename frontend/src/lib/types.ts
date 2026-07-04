export type Role = "requester" | "agent" | "manager";

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
}

export type TicketStatus = "open" | "assigned" | "escalated" | "resolved" | "closed";
export type TicketPriority = "low" | "normal" | "high" | "urgent";

export interface Ticket {
  id: number;
  title: string;
  description: string;
  requester: number;
  requester_username: string;
  assignee: number | null;
  assignee_username: string | null;
  status: TicketStatus;
  priority: TicketPriority;
  category: string;
  sla_due_at: string | null;
  created_at: string;
  updated_at: string;
  escalated_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
}

export interface TicketEvent {
  id: number;
  ticket: number;
  actor: number | null;
  actor_username: string | null;
  from_status: TicketStatus;
  to_status: TicketStatus;
  note: string;
  created_at: string;
}

export interface Comment {
  id: number;
  ticket: number;
  author: number;
  author_username: string;
  body: string;
  is_internal: boolean;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
