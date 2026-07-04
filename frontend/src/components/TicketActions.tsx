"use client";

import { useState } from "react";

import { useAuth } from "../context/AuthContext";
import { api, ApiError } from "../lib/api";
import type { Ticket } from "../lib/types";

interface Props {
  ticket: Ticket;
  onChanged: () => void;
}

const buttonClass =
  "rounded-md bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50";
const secondaryClass =
  "rounded-md border border-zinc-300 px-4 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-50 disabled:opacity-50";

export default function TicketActions({ ticket, onChanged }: Props) {
  const { user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [assigneeId, setAssigneeId] = useState("");
  const [escalating, setEscalating] = useState(false);
  const [note, setNote] = useState("");

  if (!user) return null;
  const role = user.role;
  const isStaff = role === "agent" || role === "manager";

  async function act(action: string, body?: Record<string, unknown>) {
    setError(null);
    setBusy(true);
    try {
      await api(`/api/v1/tickets/${ticket.id}/${action}/`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      });
      setEscalating(false);
      setNote("");
      setAssigneeId("");
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  const canAssign = isStaff && ticket.status === "open";
  const canEscalate =
    role === "manager" && (ticket.status === "open" || ticket.status === "assigned");
  const canResolve =
    (role === "manager" || (role === "agent" && ticket.assignee === user.id)) &&
    (ticket.status === "assigned" || ticket.status === "escalated");
  const canClose =
    ticket.status === "resolved" && (role === "manager" || ticket.requester === user.id);

  if (!canAssign && !canEscalate && !canResolve && !canClose) return null;

  return (
    <div className="mt-6 rounded-lg border border-zinc-200 bg-white p-4">
      <h2 className="text-sm font-semibold uppercase text-zinc-500">Actions</h2>

      {error && (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3">
        {canAssign && (
          <>
            <button
              onClick={() => act("assign", { assignee: user.id })}
              disabled={busy}
              className={buttonClass}
            >
              Assign to me
            </button>
            {role === "manager" && (
              <span className="flex items-center gap-2">
                <input
                  value={assigneeId}
                  onChange={(e) => setAssigneeId(e.target.value)}
                  type="number"
                  min={1}
                  placeholder="User id"
                  className="w-24 rounded-md border border-zinc-300 px-2 py-1.5 text-sm focus:border-zinc-500 focus:outline-none"
                />
                <button
                  onClick={() => act("assign", { assignee: Number(assigneeId) })}
                  disabled={busy || !assigneeId}
                  className={secondaryClass}
                >
                  Assign
                </button>
              </span>
            )}
          </>
        )}

        {canEscalate && !escalating && (
          <button onClick={() => setEscalating(true)} disabled={busy} className={secondaryClass}>
            Escalate…
          </button>
        )}

        {canResolve && (
          <button onClick={() => act("resolve")} disabled={busy} className={buttonClass}>
            Resolve
          </button>
        )}

        {canClose && (
          <button onClick={() => act("close")} disabled={busy} className={buttonClass}>
            Close ticket
          </button>
        )}
      </div>

      {canEscalate && escalating && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Reason (optional)"
            className="w-64 rounded-md border border-zinc-300 px-2 py-1.5 text-sm focus:border-zinc-500 focus:outline-none"
          />
          <button
            onClick={() => act("escalate", { note })}
            disabled={busy}
            className={buttonClass}
          >
            Escalate
          </button>
          <button
            onClick={() => {
              setEscalating(false);
              setNote("");
            }}
            disabled={busy}
            className={secondaryClass}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
