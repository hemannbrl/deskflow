"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "../context/AuthContext";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return <p className="p-8 text-center text-zinc-500">Loading…</p>;
  }
  return <>{children}</>;
}
