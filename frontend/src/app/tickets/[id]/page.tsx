"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PriorityBadge, StatusBadge } from "../../../components/Badges";
import CommentThread from "../../../components/CommentThread";
import RequireAuth from "../../../components/RequireAuth";
import TicketActions from "../../../components/TicketActions";
import { ErrorBanner, Spinner } from "../../../components/ui";
import { api, ApiError } from "../../../lib/api";
import { formatDate, isSlaBreached } from "../../../lib/format";
import type { Ticket, TicketEvent } from "../../../lib/types";

function Meta({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase text-zinc-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-zinc-900">{children}</dd>
    </div>
  );
}

function Timeline({ events }: { events: TicketEvent[] }) {
  if (events.length === 0) {
    return <p className="mt-4 text-sm text-zinc-500">No status changes yet.</p>;
  }
  return (
    <ol className="mt-4 space-y-4 border-l-2 border-zinc-200 pl-4">
      {events.map((e) => (
        <li key={e.id} className="relative">
          <span className="absolute -left-[1.4rem] top-1.5 h-2.5 w-2.5 rounded-full bg-zinc-400" />
          <p className="text-sm text-zinc-900">
            <span className="font-medium">{e.from_status}</span>
            {" → "}
            <span className="font-medium">{e.to_status}</span>
            <span className="text-zinc-500"> by {e.actor_username ?? "system"}</span>
          </p>
          {e.note && <p className="mt-0.5 text-sm italic text-zinc-600">“{e.note}”</p>}
          <p className="mt-0.5 text-xs text-zinc-500">{formatDate(e.created_at)}</p>
        </li>
      ))}
    </ol>
  );
}

function TicketDetail({ id }: { id: string }) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [events, setEvents] = useState<TicketEvent[]>([]);
  const [error, setError] = useState<"notfound" | string | null>(null);

  const load = useCallback(() => {
    Promise.all([
      api<Ticket>(`/api/v1/tickets/${id}/`),
      api<TicketEvent[]>(`/api/v1/tickets/${id}/events/`),
    ])
      .then(([t, e]) => {
        setTicket(t);
        setEvents(e);
        setError(null);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setError("notfound");
        else setError(err instanceof ApiError ? err.message : "Failed to load ticket");
      });
  }, [id]);

  useEffect(load, [load]);

  if (error === "notfound") {
    return (
      <div className="mt-12 text-center">
        <p className="text-lg text-zinc-600">This ticket doesn&apos;t exist — or you don&apos;t have access to it.</p>
        <Link href="/tickets" className="mt-4 inline-block text-sm font-medium text-zinc-900 underline">
          Back to tickets
        </Link>
      </div>
    );
  }
  if (error) {
    return <ErrorBanner message={error} onRetry={load} />;
  }
  if (!ticket) {
    return <Spinner label="Loading ticket…" />;
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold text-zinc-900">
          <span className="text-zinc-400">#{ticket.id}</span> {ticket.title}
        </h1>
        <StatusBadge status={ticket.status} />
        <PriorityBadge priority={ticket.priority} />
      </div>

      <p className="mt-4 whitespace-pre-wrap rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-700">
        {ticket.description}
      </p>

      <dl className="mt-6 grid grid-cols-2 gap-4 rounded-lg border border-zinc-200 bg-white p-4 sm:grid-cols-3">
        <Meta label="Requester">{ticket.requester_username}</Meta>
        <Meta label="Assignee">{ticket.assignee_username ?? "unassigned"}</Meta>
        <Meta label="Category">{ticket.category}</Meta>
        <Meta label="Created">{formatDate(ticket.created_at)}</Meta>
        <Meta label="SLA due">
          <span className={isSlaBreached(ticket) ? "font-medium text-red-600" : undefined}>
            {formatDate(ticket.sla_due_at)}
            {isSlaBreached(ticket) && " (overdue)"}
          </span>
        </Meta>
        {ticket.escalated_at && <Meta label="Escalated">{formatDate(ticket.escalated_at)}</Meta>}
        {ticket.resolved_at && <Meta label="Resolved">{formatDate(ticket.resolved_at)}</Meta>}
        {ticket.closed_at && <Meta label="Closed">{formatDate(ticket.closed_at)}</Meta>}
      </dl>

      <TicketActions ticket={ticket} onChanged={load} />

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-zinc-900">History</h2>
        <Timeline events={events} />
      </section>

      <CommentThread ticketId={id} />
    </>
  );
}

export default function TicketDetailPage() {
  const params = useParams<{ id: string }>();
  return (
    <RequireAuth>
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">
        <Link href="/tickets" className="text-sm text-zinc-500 hover:text-zinc-900">
          ← All tickets
        </Link>
        <div className="mt-4">
          <TicketDetail id={params.id} />
        </div>
      </main>
    </RequireAuth>
  );
}
