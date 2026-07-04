import RequireAuth from "../../components/RequireAuth";

export default function TicketsPage() {
  return (
    <RequireAuth>
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        <h1 className="text-2xl font-semibold text-zinc-900">Tickets</h1>
        <p className="mt-4 text-zinc-500">Ticket list coming soon.</p>
      </main>
    </RequireAuth>
  );
}
