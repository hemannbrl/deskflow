import type { TicketPriority, TicketStatus } from "../lib/types";

const STATUS_STYLES: Record<TicketStatus, string> = {
  open: "bg-emerald-100 text-emerald-800",
  assigned: "bg-blue-100 text-blue-800",
  escalated: "bg-red-100 text-red-800",
  resolved: "bg-violet-100 text-violet-800",
  closed: "bg-zinc-200 text-zinc-600",
};

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  low: "bg-zinc-100 text-zinc-600",
  normal: "bg-sky-100 text-sky-800",
  high: "bg-amber-100 text-amber-800",
  urgent: "bg-red-100 text-red-800",
};

const badgeClass = "inline-block rounded-full px-2 py-0.5 text-xs font-medium";

export function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`${badgeClass} ${STATUS_STYLES[status]}`}>{status}</span>;
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return <span className={`${badgeClass} ${PRIORITY_STYLES[priority]}`}>{priority}</span>;
}
