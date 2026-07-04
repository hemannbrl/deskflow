"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";
import type { Role } from "../lib/types";

const ROLE_STYLES: Record<Role, string> = {
  requester: "bg-zinc-100 text-zinc-700",
  agent: "bg-blue-100 text-blue-700",
  manager: "bg-purple-100 text-purple-700",
};

export default function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
        <Link href={user ? "/tickets" : "/"} className="text-lg font-bold text-zinc-900">
          deskflow
        </Link>
        {user && (
          <div className="flex items-center gap-3 text-sm">
            <span className="font-medium text-zinc-700">{user.username}</span>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${ROLE_STYLES[user.role]}`}>
              {user.role}
            </span>
            <button
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="rounded-md border border-zinc-300 px-3 py-1 text-zinc-600 transition-colors hover:bg-zinc-50"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
