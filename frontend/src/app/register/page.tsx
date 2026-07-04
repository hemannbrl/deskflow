"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../lib/api";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string | null>>({});
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setBusy(true);
    try {
      await register(username, email, password);
      router.push("/tickets");
    } catch (err) {
      if (err instanceof ApiError) {
        const fields = {
          username: err.fieldError("username"),
          email: err.fieldError("email"),
          password: err.fieldError("password"),
        };
        setFieldErrors(fields);
        if (!fields.username && !fields.email && !fields.password) setError(err.message);
      } else {
        setError("Something went wrong");
      }
      setBusy(false);
    }
  }

  const inputClass =
    "mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-zinc-500 focus:outline-none";

  return (
    <main className="mx-auto w-full max-w-sm flex-1 px-6 py-16">
      <h1 className="text-2xl font-semibold text-zinc-900">Create an account</h1>
      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}
        <label className="block text-sm font-medium text-zinc-700">
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
            className={inputClass}
          />
          {fieldErrors.username && (
            <span className="mt-1 block text-xs text-red-600">{fieldErrors.username}</span>
          )}
        </label>
        <label className="block text-sm font-medium text-zinc-700">
          Email <span className="font-normal text-zinc-400">(optional)</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
          {fieldErrors.email && (
            <span className="mt-1 block text-xs text-red-600">{fieldErrors.email}</span>
          )}
        </label>
        <label className="block text-sm font-medium text-zinc-700">
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className={inputClass}
          />
          {fieldErrors.password && (
            <span className="mt-1 block text-xs text-red-600">{fieldErrors.password}</span>
          )}
        </label>
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-md bg-zinc-900 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
        >
          {busy ? "Creating account…" : "Register"}
        </button>
      </form>
      <p className="mt-6 text-sm text-zinc-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          Sign in
        </Link>
      </p>
    </main>
  );
}
