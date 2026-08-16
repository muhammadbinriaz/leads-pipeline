"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearToken, getToken } from "@/lib/api";
import type { User } from "@/lib/types";

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<User>("/api/auth/me")
      .then(setUser)
      .catch(() => router.replace("/login"));
  }, [router]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  const nav = [
    { href: "/campaigns", label: "Campaigns" },
    { href: "/campaigns/new", label: "New campaign" },
    { href: "/settings", label: "Settings" },
  ];

  return (
    <div className="shell">
      <aside className="rail">
        <Link href="/campaigns" className="brand">
          <span className="mark">◎</span>
          <span>
            <strong>Signal</strong>
            <em>Lead workspace</em>
          </span>
        </Link>
        <nav>
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href || (item.href !== "/campaigns" && pathname.startsWith(item.href)) ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="rail-foot">
          <span>{user?.email}</span>
          <button type="button" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="canvas">{children}</main>
    </div>
  );
}
