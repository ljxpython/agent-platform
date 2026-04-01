import { EmptyState } from "@/components/platform/empty-state";
import { PageHeader } from "@/components/platform/page-header";
import { PlatformPage } from "@/components/platform/platform-page";

export default function RuntimePage() {
  return (
    <PlatformPage>
      <PageHeader
        description="Runtime 页面已经纳入 v2 工作台导航，但详细能力还没有迁移。这里先保留统一母版和占位说明。"
        eyebrow="Advanced"
        title="Runtime"
      />
      <EmptyState
        description="Runtime 工作区将在后续阶段迁入。当前优先完成 management 方向的 P0 页面和基础上下文能力。"
        title="Runtime migration pending"
      />
    </PlatformPage>
  );
}
