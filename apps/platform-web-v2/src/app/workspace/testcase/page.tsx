import { EmptyState } from "@/components/platform/empty-state";
import { PageHeader } from "@/components/platform/page-header";
import { PlatformPage } from "@/components/platform/platform-page";

export default function TestcasePage() {
  return (
    <PlatformPage>
      <PageHeader
        description="Testcase 属于后续复杂工作区迁移范围。这里先接入 v2 壳子，后面再逐步迁 generate / cases / documents。"
        eyebrow="Advanced"
        title="Testcase"
      />
      <EmptyState
        description="Testcase 工作区将在 P2 阶段迁移，当前重点仍然是管理页、登录和项目上下文。"
        title="Testcase migration pending"
      />
    </PlatformPage>
  );
}
