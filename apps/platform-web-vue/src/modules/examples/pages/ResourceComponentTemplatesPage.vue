<script setup lang="ts">
import PageHeader from '@/components/layout/PageHeader.vue'
import MetricCard from '@/components/platform/MetricCard.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import Sub2apiTemplateGallery from '@/modules/examples/components/Sub2apiTemplateGallery.vue'
import { recommendedTemplateStats, templateSceneStats } from '@/modules/examples/ui-assets-curation'
import { sub2apiTemplateStats } from '@/modules/examples/ui-assets-catalog'

const stats = [
  {
    label: '组件模板数',
    value: sub2apiTemplateStats.components,
    hint: '组件层模板最密，DataTable、Pagination、Dialog、图表、领域组件都拆开了。',
    icon: 'users',
    tone: 'success'
  },
  {
    label: '推荐模板数',
    value: recommendedTemplateStats.components,
    hint: '默认先给出壳层、列表体系、弹层和图表这些最值得直接借的组件骨架。',
    icon: 'folder',
    tone: 'primary'
  },
  {
    label: '场景模板集',
    value: templateSceneStats.components.sceneCount,
    hint: '壳层系统区、列表工具栏、弹窗编辑流、图表区和认证安全组件都按场景收好了。',
    icon: 'sparkle',
    tone: 'warning'
  }
] as const
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Resources"
      title="组件模板"
      description="这里只放组件级模板。后续开发者要借 DataTable、Dialog、Pagination、领域弹窗、图表或布局壳，不要再混进页面模板里找。"
    />

    <StateBanner
      title="组件模板已收敛为三层资源页"
      description="组件模板数量最多，所以默认不再直接扔出全部档案，而是先从推荐模板和场景模板开始，最后才看原始档案。"
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
      mode="components"
      eyebrow="Component Templates"
      title="Sub2api 组件模板库"
      description="通用组件、布局壳、图表、账号领域组件、用户领域组件和各类管理弹窗都在这里，但默认先收敛成推荐模板和场景模板，避免开发者面对一墙同质化卡片。"
      search-placeholder="搜索组件名、源码路径或可借用点"
    />
  </section>
</template>
