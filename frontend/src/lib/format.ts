import type { Ticket } from "./types";

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function isSlaBreached(ticket: Ticket): boolean {
  if (!ticket.sla_due_at) return false;
  if (ticket.status === "resolved" || ticket.status === "closed") return false;
  return new Date(ticket.sla_due_at).getTime() < Date.now();
}
