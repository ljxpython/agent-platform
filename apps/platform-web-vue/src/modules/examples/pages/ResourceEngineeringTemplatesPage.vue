<script setup lang="ts">
import PageHeader from '@/components/layout/PageHeader.vue'
import MetricCard from '@/components/platform/MetricCard.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import Sub2apiTemplateGallery from '@/modules/examples/components/Sub2apiTemplateGallery.vue'
import { recommendedTemplateStats, templateSceneStats } from '@/modules/examples/ui-assets-curation'
import { sub2apiTemplateStats } from '@/modules/examples/ui-assets-catalog'

const stats = [
  {
    label: '工程模板数',
    value: sub2apiTemplateStats.engineering,
    hint: 'API、Pinia、router、composable、i18n、utils 等工程支撑都沉淀进来了。',
    icon: 'runtime',
    tone: 'warning'
  },
  {
    label: '推荐模板数',
    value: recommendedTemplateStats.engineering,
    hint: 'API client、状态收口、路由接线和 i18n 这批最值钱的工程骨架已被优先抽出。',
    icon: 'folder',
    tone: 'primary'
  },
  {
    label: '场景模板集',
    value: templateSceneStats.engineering.sceneCount,
    hint: '接口边界、列表状态、路由导航、启动与国际化都已经按场景分好了。',
    icon: 'sparkle',
    tone: 'success'
  }
] as const
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Resources"
      title="工程模板"
      description="这里只放工程层模板。后续开发者要学 API 封装、状态管理、路由组织、composable 写法和 i18n 接线，就在这边看。"
    />

    <StateBanner
      title="工程模板已收敛为三层资源页"
      description="工程层最容易被全量文件淹没，所以现在默认先看推荐模板和场景模板，再决定是否进入原始档案查具体实现。"
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
      mode="engineering"
      eyebrow="Engineering Templates"
      title="Sub2api 工程模板库"
      description="接口、store、router、composable、i18n、styles、utils 这些工程模板仍然都在，但默认先展示最值得借的骨架和场景集，减少翻原始文件的噪音。"
      search-placeholder="搜索文件名、路径、工程标签或借用点"
    />
  </section>
</template>
