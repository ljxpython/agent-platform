import { EmptyState } from "@/components/platform/empty-state";
import { PageHeader } from "@/components/platform/page-header";
import { PlatformPage } from "@/components/platform/platform-page";

export default function ChatPage() {
  return (
    <PlatformPage>
      <PageHeader
        description="Chat 工作区属于后续 P2 范围，当前先占住路由和新工作台母版，避免 v2 导航出现死链。"
        eyebrow="Advanced"
        title="Chat"
      />
      <EmptyState
        description="Chat 页面会在 management 页迁移稳定后再继续承接。当前先保留统一布局与主题体系。"
        title="Chat migration pending"
      />
    </PlatformPage>
  );
}
