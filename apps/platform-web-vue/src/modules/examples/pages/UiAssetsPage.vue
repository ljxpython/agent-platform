<script setup lang="ts">
import PageHeader from '@/components/layout/PageHeader.vue'
import SurfaceCard from '@/components/base/SurfaceCard.vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import MetricCard from '@/components/platform/MetricCard.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import Sub2apiTemplateShowcase from '@/modules/examples/components/Sub2apiTemplateShowcase.vue'
import { recommendedTemplateStats, templateSceneStats } from '@/modules/examples/ui-assets-curation'
import { sub2apiTemplateGroups, sub2apiTemplateStats } from '@/modules/examples/ui-assets-catalog'

const isDev = import.meta.env.DEV
const totalSceneCount =
  templateSceneStats.pages.sceneCount +
  templateSceneStats.components.sceneCount +
  templateSceneStats.engineering.sceneCount

const stats = [
  {
    label: '推荐模板',
    value: recommendedTemplateStats.total,
    hint: '默认先展示这批首选模板，解决“开发时到底该选谁”这个问题。',
    icon: 'folder',
    tone: 'primary'
  },
  {
    label: '场景模板集',
    value: totalSceneCount,
    hint: '把页面、组件、工程模板按真实开发场景重新收口，不再只按目录看文件。',
    icon: 'users',
    tone: 'success'
  },
  {
    label: '原始档案',
    value: sub2apiTemplateStats.pages + sub2apiTemplateStats.components + sub2apiTemplateStats.engineering,
    hint: '完整保留上游模板档案，只有需要深挖源码时才建议进入。',
    icon: 'runtime',
    tone: 'warning'
  },
  {
    label: '资源页',
    value: 4,
    hint: '总览页加三个模板子页，结构继续保持清晰，不回到单页大杂烩。',
    icon: 'sparkle',
    tone: 'primary'
  }
] as const

const resourceCards = [
  {
    title: '页面模板',
    description: '专门看页面级模板。列表页、看板页、认证页、公开页、向导页都拆开了，后续开发者直接按页面借壳。',
    to: '/workspace/resources/pages',
    label: '进入页面模板',
    icon: 'folder',
    tone: 'primary',
    count: sub2apiTemplateStats.pages,
    groupCount: sub2apiTemplateGroups.pages.length
  },
  {
    title: '组件模板',
    description: '专门看组件级模板。DataTable、Pagination、Dialog、图表、账号/用户领域组件都在这边单独挑。',
    to: '/workspace/resources/components',
    label: '进入组件模板',
    icon: 'users',
    tone: 'success',
    count: sub2apiTemplateStats.components,
    groupCount: sub2apiTemplateGroups.components.length
  },
  {
    title: '工程模板',
    description: '专门看工程层模板。接口、Pinia、router、composable、i18n、utils 都收进来了，方便整套学习。',
    to: '/workspace/resources/engineering',
    label: '进入工程模板',
    icon: 'runtime',
    tone: 'warning',
    count: sub2apiTemplateStats.engineering,
    groupCount: sub2apiTemplateGroups.engineering.length
  }
] as const
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Resources"
      title="资源总览"
      description="这里现在只做汇总，不再承载全部模板列表。你可以从这里进入页面模板、组件模板和工程模板三个独立资源页。"
    />

    <StateBanner
      :title="isDev ? '当前为开发环境资源总览页' : '当前为隐藏资源总览页'"
      :description="
        isDev
          ? 'Resources 已经拆成多页面结构，并且每个模板子页都采用 推荐模板 / 场景模板 / 原始档案 三层结构。'
          : '生产环境默认不暴露这类研发资源位，但路由仍然保留，方便后续扩展。'
      "
      variant="info"
    />

    <div class="grid gap-4 xl:grid-cols-4">
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

    <div class="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_360px]">
      <SurfaceCard>
        <div class="pw-page-eyebrow">
          Resource Pages
        </div>
        <h2 class="mt-1 text-xl font-semibold text-gray-900 dark:text-white">
          模板入口
        </h2>
        <p class="mt-2 max-w-4xl text-sm leading-7 text-gray-500 dark:text-dark-300">
          以后开发者不需要在一页里滚 260 多个模板。先判断自己要找的是页面、组件还是工程支撑，再进入对应资源页，从推荐模板和场景模板开始挑。
        </p>

        <div class="mt-6 grid gap-4 xl:grid-cols-3">
          <article
            v-for="card in resourceCards"
            :key="card.to"
            class="rounded-[24px] border border-gray-100 bg-white/80 p-5 shadow-soft dark:border-dark-800 dark:bg-dark-950/35"
          >
            <div class="flex items-start justify-between gap-4">
              <div
                class="flex h-12 w-12 items-center justify-center rounded-2xl"
                :class="
                  card.tone === 'success'
                    ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-300'
                    : card.tone === 'warning'
                      ? 'bg-amber-100 text-amber-600 dark:bg-amber-950/40 dark:text-amber-300'
                      : 'bg-primary-100 text-primary-600 dark:bg-primary-950/40 dark:text-primary-300'
                "
              >
                <BaseIcon
                  :name="card.icon as never"
                  size="md"
                />
              </div>
              <div class="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-600 dark:border-dark-700 dark:bg-dark-900 dark:text-dark-200">
                {{ card.groupCount }} 组 / {{ card.count }} 个
              </div>
            </div>

            <h3 class="mt-4 text-lg font-semibold text-gray-900 dark:text-white">
              {{ card.title }}
            </h3>
            <p class="mt-2 text-sm leading-7 text-gray-500 dark:text-dark-300">
              {{ card.description }}
            </p>

            <div class="mt-5">
              <router-link
                :to="card.to"
                class="pw-btn pw-btn-secondary inline-flex items-center gap-2"
              >
                <BaseIcon
                  name="chevron-right"
                  size="sm"
                />
                {{ card.label }}
              </router-link>
            </div>
          </article>
        </div>
      </SurfaceCard>

      <SurfaceCard>
        <div class="pw-page-eyebrow">
          Usage Guide
        </div>
        <h2 class="mt-1 text-xl font-semibold text-gray-900 dark:text-white">
          使用方式
        </h2>

        <div class="mt-5 space-y-3 text-sm leading-7 text-gray-500 dark:text-dark-300">
          <div class="rounded-[20px] border border-gray-100 bg-gray-50/80 p-4 dark:border-dark-800 dark:bg-dark-950/45">
            1. 先判断你要借的是页面骨架、局部组件还是工程支撑。
          </div>
          <div class="rounded-[20px] border border-gray-100 bg-gray-50/80 p-4 dark:border-dark-800 dark:bg-dark-950/45">
            2. 进入对应资源页，先看推荐模板；如果还不确定，再切到场景模板。
          </div>
          <div class="rounded-[20px] border border-gray-100 bg-gray-50/80 p-4 dark:border-dark-800 dark:bg-dark-950/45">
            3. 真要深挖实现细节时，再进入原始档案，按分组或搜索找源码。
          </div>
          <div class="rounded-[20px] border border-gray-100 bg-gray-50/80 p-4 dark:border-dark-800 dark:bg-dark-950/45">
            4. 借的是结构、节奏和拆分方式，不是把上游业务语义整页硬搬。
          </div>
        </div>
      </SurfaceCard>
    </div>

    <Sub2apiTemplateShowcase
      mode="pages"
      title="页面模板精选"
      description="资源总览页不再把全部页面模板一股脑塞一起，但至少应该把代表性的页面模板直接亮出来，避免看起来像只有目录没有内容。"
      action-to="/workspace/resources/pages"
      action-label="查看全部页面模板"
    />

    <Sub2apiTemplateShowcase
      mode="components"
      title="组件模板精选"
      description="把 DataTable、Dialog、图表、账号/用户领域组件的代表模板先摆出来，开发者一进来就能看到能借什么。"
      action-to="/workspace/resources/components"
      action-label="查看全部组件模板"
    />

    <Sub2apiTemplateShowcase
      mode="engineering"
      title="工程模板精选"
      description="接口层、状态层、路由层、组合式逻辑和样式组织方式也要给出代表模板，不然总览页的信息层级还是会偏空。"
      action-to="/workspace/resources/engineering"
      action-label="查看全部工程模板"
    />
  </section>
</template>
