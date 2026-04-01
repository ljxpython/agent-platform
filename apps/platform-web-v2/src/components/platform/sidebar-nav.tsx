"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_GROUPS = [
  {
    label: "Workspace",
    items: [
      { href: "/workspace/overview", label: "Overview" },
      { href: "/workspace/projects", label: "Projects" },
      { href: "/workspace/assistants", label: "Assistants" },
      { href: "/workspace/users", label: "Users" },
    ],
  },
  {
    label: "Advanced",
    items: [
      { href: "/workspace/graphs", label: "Graphs" },
      { href: "/workspace/runtime", label: "Runtime" },
      { href: "/workspace/threads", label: "Threads" },
      { href: "/workspace/chat", label: "Chat" },
      { href: "/workspace/testcase", label: "Testcase" },
    ],
  },
] as const;

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <>
      {NAV_GROUPS.map((group) => (
        <section key={group.label} className="workspace-shell__nav-group">
          <div className="workspace-shell__nav-label">{group.label}</div>
          <nav className="workspace-shell__nav-list" aria-label={group.label}>
            {group.items.map((item) => {
              const active =
                pathname === item.href ||
                (item.href !== "/workspace/overview" &&
                  pathname?.startsWith(`${item.href}/`));
              return (
                <Link
                  key={item.href}
                  className={`workspace-shell__nav-item ${active ? "is-active" : ""}`}
                  href={item.href}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </section>
      ))}
    </>
  );
}
