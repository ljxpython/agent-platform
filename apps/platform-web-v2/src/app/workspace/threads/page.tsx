import { EmptyState } from "@/components/platform/empty-state";
import { PageHeader } from "@/components/platform/page-header";
import { PlatformPage } from "@/components/platform/platform-page";

export default function ThreadsPage() {
  return (
    <PlatformPage>
      <PageHeader
        description="Threads 页面后续会承接旧平台的线程管理与会话审计能力。当前先统一到新的工作台布局里。"
        eyebrow="Advanced"
        title="Threads"
      />
      <EmptyState
        description="Threads 还未开始迁移，当前阶段先完成基础管理页和项目上下文链路。"
        title="Threads migration pending"
      />
    </PlatformPage>
  );
}
