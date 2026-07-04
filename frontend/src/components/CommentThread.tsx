"use client";

import { useCallback, useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { api, ApiError } from "../lib/api";
import { formatDate } from "../lib/format";
import type { Comment } from "../lib/types";
import { Spinner } from "./ui";

export default function CommentThread({ ticketId }: { ticketId: string }) {
  const { user } = useAuth();
  const isStaff = user?.role === "agent" || user?.role === "manager";

  const [comments, setComments] = useState<Comment[] | null>(null);
  const [body, setBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api<Comment[]>(`/api/v1/tickets/${ticketId}/comments/`)
      .then(setComments)
      .catch(() => setError("Failed to load comments"));
  }, [ticketId]);

  useEffect(load, [load]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api(`/api/v1/tickets/${ticketId}/comments/`, {
        method: "POST",
        body: JSON.stringify({ body, is_internal: isStaff && isInternal }),
      });
      setBody("");
      setIsInternal(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to post comment");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold text-zinc-900">Comments</h2>

      {error && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      {!comments ? (
        <Spinner label="Loading comments…" />
      ) : comments.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-500">No comments yet.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {comments.map((c) => (
            <li
              key={c.id}
              className={`rounded-lg border p-3 ${
                c.is_internal ? "border-amber-200 bg-amber-50" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <span className="font-medium text-zinc-700">{c.author_username}</span>
                <span>{formatDate(c.created_at)}</span>
                {c.is_internal && (
                  <span className="rounded-full bg-amber-200 px-2 py-0.5 font-medium text-amber-800">
                    internal
                  </span>
                )}
              </div>
              <p className="mt-1.5 whitespace-pre-wrap text-sm text-zinc-800">{c.body}</p>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="mt-4">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          rows={3}
          placeholder="Write a comment…"
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none"
        />
        <div className="mt-2 flex items-center justify-between">
          {isStaff ? (
            <label className="flex items-center gap-2 text-sm text-zinc-600">
              <input
                type="checkbox"
                checked={isInternal}
                onChange={(e) => setIsInternal(e.target.checked)}
                className="h-4 w-4 rounded border-zinc-300"
              />
              Internal note (hidden from the requester)
            </label>
          ) : (
            <span />
          )}
          <button
            type="submit"
            disabled={busy || !body.trim()}
            className="rounded-md bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
          >
            {busy ? "Posting…" : "Post"}
          </button>
        </div>
      </form>
    </section>
  );
}
