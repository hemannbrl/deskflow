"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PriorityBadge, StatusBadge } from "../../components/Badges";
import RequireAuth from "../../components/RequireAuth";
import { EmptyState, ErrorBanner, Spinner } from "../../components/ui";
import { api, ApiError } from "../../lib/api";
import { formatDate, isSlaBreached } from "../../lib/format";
import type { Paginated, Ticket } from "../../lib/types";

const PAGE_SIZE = 20;

function TicketList() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Ticket> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api<Paginated<Ticket>>(`/api/v1/tickets/?page=${page}`)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load tickets"),
      );
  }, [page]);

  useEffect(load, [load]);

  if (error) {
    return <ErrorBanner message={error} onRetry={load} />;
  }
  if (!data) {
    return <Spinner label="Loading tickets…" />;
  }
  if (data.count === 0) {
    return (
      <EmptyState
        title="No tickets yet."
        actionHref="/tickets/new"
        actionLabel="Open your first ticket"
      />
    );
  }

  const lastPage = Math.ceil(data.count / PAGE_SIZE);

  return (
    <>
      <div className="mt-6 overflow-x-auto rounded-lg border border-zinc-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-200 text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Priority</th>
              <th className="hidden px-4 py-3 md:table-cell">Category</th>
              <th className="hidden px-4 py-3 md:table-cell">Created</th>
              <th className="hidden px-4 py-3 sm:table-cell">SLA due</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((t) => (
              <tr key={t.id} className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50">
                <td className="px-4 py-3 text-zinc-500">{t.id}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/tickets/${t.id}`}
                    className="font-medium text-zinc-900 hover:underline"
                  >
                    {t.title}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-4 py-3">
                  <PriorityBadge priority={t.priority} />
                </td>
                <td className="hidden px-4 py-3 text-zinc-600 md:table-cell">{t.category}</td>
                <td className="hidden px-4 py-3 text-zinc-600 md:table-cell">
                  {formatDate(t.created_at)}
                </td>
                <td
                  className={`hidden px-4 py-3 sm:table-cell ${
                    isSlaBreached(t) ? "font-medium text-red-600" : "text-zinc-600"
                  }`}
                >
                  {formatDate(t.sla_due_at)}
                  {isSlaBreached(t) && " (overdue)"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {lastPage > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-zinc-600">
          <button
            onClick={() => setPage((p) => p - 1)}
            disabled={!data.previous}
            className="rounded-md border border-zinc-300 px-3 py-1.5 disabled:opacity-40"
          >
            Previous
          </button>
          <span>
            Page {page} of {lastPage}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!data.next}
            className="rounded-md border border-zinc-300 px-3 py-1.5 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </>
  );
}

export default function TicketsPage() {
  return (
    <RequireAuth>
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-zinc-900">Tickets</h1>
          <Link
            href="/tickets/new"
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
          >
            New ticket
          </Link>
        </div>
        <TicketList />
      </main>
    </RequireAuth>
  );
}
