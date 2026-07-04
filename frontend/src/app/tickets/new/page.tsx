"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import RequireAuth from "../../../components/RequireAuth";
import { api, ApiError } from "../../../lib/api";
import type { Ticket, TicketPriority } from "../../../lib/types";

const PRIORITIES: TicketPriority[] = ["low", "normal", "high", "urgent"];

function NewTicketForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TicketPriority>("normal");
  const [category, setCategory] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string | null>>({});
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setBusy(true);
    try {
      const ticket = await api<Ticket>("/api/v1/tickets/", {
        method: "POST",
        body: JSON.stringify({
          title,
          description,
          priority,
          ...(category.trim() ? { category: category.trim() } : {}),
        }),
      });
      router.push(`/tickets/${ticket.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        const fields = {
          title: err.fieldError("title"),
          description: err.fieldError("description"),
          category: err.fieldError("category"),
        };
        setFieldErrors(fields);
        if (!fields.title && !fields.description && !fields.category) setError(err.message);
      } else {
        setError("Something went wrong");
      }
      setBusy(false);
    }
  }

  const inputClass =
    "mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:border-zinc-500 focus:outline-none";

  return (
    <form onSubmit={handleSubmit} className="mt-6 max-w-xl space-y-4">
      {error && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}
      <label className="block text-sm font-medium text-zinc-700">
        Title
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          autoFocus
          placeholder="Short summary of the problem"
          className={inputClass}
        />
        {fieldErrors.title && (
          <span className="mt-1 block text-xs text-red-600">{fieldErrors.title}</span>
        )}
      </label>
      <label className="block text-sm font-medium text-zinc-700">
        Description
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={5}
          placeholder="What happened? What did you expect?"
          className={inputClass}
        />
        {fieldErrors.description && (
          <span className="mt-1 block text-xs text-red-600">{fieldErrors.description}</span>
        )}
      </label>
      <div className="flex gap-4">
        <label className="block flex-1 text-sm font-medium text-zinc-700">
          Priority
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as TicketPriority)}
            className={inputClass}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="block flex-1 text-sm font-medium text-zinc-700">
          Category <span className="font-normal text-zinc-400">(optional)</span>
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            maxLength={40}
            placeholder="e.g. network, hardware"
            className={inputClass}
          />
          {fieldErrors.category && (
            <span className="mt-1 block text-xs text-red-600">{fieldErrors.category}</span>
          )}
        </label>
      </div>
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
        >
          {busy ? "Opening…" : "Open ticket"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/tickets")}
          className="rounded-md border border-zinc-300 px-5 py-2 text-sm text-zinc-600 transition-colors hover:bg-zinc-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function NewTicketPage() {
  return (
    <RequireAuth>
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        <h1 className="text-2xl font-semibold text-zinc-900">New ticket</h1>
        <NewTicketForm />
      </main>
    </RequireAuth>
  );
}
