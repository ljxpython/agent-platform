<script setup lang="ts">
import PageHeader from '@/components/layout/PageHeader.vue'
import MetricCard from '@/components/platform/MetricCard.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import Sub2apiTemplateGallery from '@/modules/examples/components/Sub2apiTemplateGallery.vue'
import { recommendedTemplateStats, templateSceneStats } from '@/modules/examples/ui-assets-curation'
import { sub2apiTemplateStats } from '@/modules/examples/ui-assets-catalog'

const stats = [
  {
    label: '页面模板数',
    value: sub2apiTemplateStats.pages,
    hint: '把上游页面母版整库拆开，方便直接按页挑模板。',
    icon: 'folder',
    tone: 'primary'
  },
  {
    label: '推荐模板数',
    value: recommendedTemplateStats.pages,
    hint: '默认优先展示这批首选页面骨架，减少同类页面反复横跳。',
    icon: 'overview',
    tone: 'success'
  },
  {
    label: '场景模板集',
    value: templateSceneStats.pages.sceneCount,
    hint: '后台列表、总览监控、认证引导、用户工作台这些场景已经单独收口。',
    icon: 'sparkle',
    tone: 'warning'
  }
] as const
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Resources"
      title="页面模板"
      description="这里只放页面级模板。后续开发者要找完整页面骨架、列表页节奏、看板页结构和认证页组织方式，就在这挑。"
    />

    <StateBanner
      title="页面模板已收敛为三层资源页"
      description="默认先看推荐模板，再按场景找页面骨架，只有需要深挖时才进入原始档案。这样不会再被整库页面模板直接淹没。"
      variant="info"
    />

    <div class="grid gap-4 xl:grid-cols-3">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :hint="item.hint"
        :icon="item.icon"
        :tone="item.tone"
      />
    </div>

    <Sub2apiTemplateGallery
      mode="pages"
      eyebrow="Page Templates"
      title="Sub2api 页面模板库"
      description="后台管理页、运维监控页、认证页、公开页和用户工作台模板都在这里，但默认先给推荐模板和场景模板，不再让人直接陷进整库 views。"
      search-placeholder="搜索页面名、源码路径或原始路由"
    />
  </section>
</template>
