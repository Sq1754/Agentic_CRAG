"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#060608]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all duration-300">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 1L13 4V10L7 13L1 10V4L7 1Z" stroke="white" strokeWidth="1.5" fill="none"/>
              <path d="M7 1L7 13M1 4L13 10M13 4L1 10" stroke="white" strokeWidth="1" opacity="0.5"/>
            </svg>
          </div>
          <span className="text-sm font-semibold text-white tracking-tight">DocuMind</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {user ? (
            <>
              <Link
                href="/dashboard"
                className="rounded-md px-3 py-1.5 text-sm text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-all"
              >
                Dashboard
              </Link>
              <div className="mx-2 h-4 w-px bg-zinc-800" />
              <span className="text-sm text-zinc-500 mr-2">{user.name}</span>
              <button
                onClick={logout}
                className="rounded-md border border-zinc-800 px-3 py-1.5 text-sm text-zinc-400 hover:border-zinc-700 hover:text-white transition-all"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-md px-3 py-1.5 text-sm text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-all"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="ml-1 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-500 shadow-lg shadow-blue-600/20 transition-all"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
