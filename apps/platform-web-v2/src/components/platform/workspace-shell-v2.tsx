import type { ReactNode } from "react";

import { ThemeToggle } from "@/components/platform/theme-toggle";

const NAV_GROUPS = [
  {
    label: "Workspace",
    items: ["Overview", "Projects", "Assistants", "Users", "Audit"],
  },
  {
    label: "Advanced",
    items: ["Runtime", "Threads", "Chat", "Testcase"],
  },
] as const;

export function WorkspaceShellV2({ children }: { children: ReactNode }) {
  return (
    <div className="workspace-shell">
      <aside className="workspace-shell__sidebar">
        <div className="workspace-shell__brand">
          <div className="workspace-shell__brand-mark">PW</div>
          <div>
            <div className="workspace-shell__brand-title">Platform Workspace</div>
            <div className="workspace-shell__brand-subtitle">enterprise console</div>
          </div>
        </div>

        {NAV_GROUPS.map((group, index) => (
          <section key={group.label} className="workspace-shell__nav-group">
            <div className="workspace-shell__nav-label">{group.label}</div>
            <nav className="workspace-shell__nav-list" aria-label={group.label}>
              {group.items.map((item, itemIndex) => (
                <a
                  key={item}
                  className={`workspace-shell__nav-item ${index === 0 && itemIndex === 0 ? "is-active" : ""}`}
                  href="#"
                >
                  {item}
                </a>
              ))}
            </nav>
          </section>
        ))}

        <div className="workspace-shell__sidebar-footer">
          <div className="workspace-shell__workspace-card">
            <div className="workspace-shell__workspace-name">Byte AI Lab</div>
            <div className="workspace-shell__workspace-meta">Shanghai Workspace</div>
          </div>
        </div>
      </aside>

      <div className="workspace-shell__main">
        <header className="workspace-shell__topbar">
          <div className="workspace-shell__context">
            <span className="workspace-shell__chip">Workspace</span>
            <span className="workspace-shell__chip">Project: 智能测试平台</span>
            <span className="workspace-shell__chip">Role: admin</span>
          </div>

          <div className="workspace-shell__topbar-actions">
            <ThemeToggle />
          </div>
        </header>

        <main className="workspace-shell__content">{children}</main>
      </div>
    </div>
  );
}
