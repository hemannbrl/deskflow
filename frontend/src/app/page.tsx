import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 bg-zinc-50 px-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-zinc-900">deskflow</h1>
      <p className="max-w-md text-lg text-zinc-600">
        IT help desk and ticketing. Open tickets, track their progress, and never miss
        an SLA.
      </p>
      <Link
        href="/login"
        className="rounded-lg bg-zinc-900 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
      >
        Sign in
      </Link>
    </div>
  );
}
