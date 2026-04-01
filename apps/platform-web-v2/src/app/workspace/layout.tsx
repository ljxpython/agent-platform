import type { ReactNode } from "react";

import { WorkspaceGuard } from "@/components/platform/workspace-guard";
import { WorkspaceShellV2 } from "@/components/platform/workspace-shell-v2";
import { WorkspaceProvider } from "@/providers/WorkspaceProvider";

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <WorkspaceGuard>
      <WorkspaceProvider>
        <WorkspaceShellV2>{children}</WorkspaceShellV2>
      </WorkspaceProvider>
    </WorkspaceGuard>
  );
}
