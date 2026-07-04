import Link from "next/link";

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="mt-8 flex items-center justify-center gap-3 text-zinc-500">
      <span
        aria-hidden
        className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-600"
      />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="mt-6 flex items-center justify-between gap-4 rounded-md bg-red-50 px-4 py-3">
      <p className="text-sm text-red-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="shrink-0 rounded-md border border-red-200 px-3 py-1 text-sm font-medium text-red-700 transition-colors hover:bg-red-100"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  actionHref,
  actionLabel,
}: {
  title: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="mt-12 rounded-lg border border-dashed border-zinc-300 py-12 text-center">
      <p className="text-zinc-500">{title}</p>
      {actionHref && actionLabel && (
        <Link
          href={actionHref}
          className="mt-4 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
