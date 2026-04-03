<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import BaseIcon from '@/components/base/BaseIcon.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const { t } = useI18n()
const workspaceStore = useWorkspaceStore()
</script>

<template>
  <label class="inline-flex items-center gap-2 rounded-2xl border border-white/60 bg-white/80 px-3 py-2 shadow-soft backdrop-blur dark:border-dark-700 dark:bg-dark-900/70">
    <BaseIcon
      name="project"
      size="sm"
      class="text-primary-500 dark:text-primary-400"
    />
    <span class="hidden text-xs font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400 lg:inline">
      {{ t('common.project') }}
    </span>
    <div class="relative">
      <select
        class="min-w-[150px] appearance-none bg-transparent py-0.5 pr-5 text-sm font-semibold text-gray-800 outline-none dark:text-gray-100"
        :value="workspaceStore.currentProjectId"
        :disabled="!workspaceStore.projects.length"
        @change="workspaceStore.setProjectId(($event.target as HTMLSelectElement).value)"
      >
        <option
          v-if="!workspaceStore.projects.length"
          value=""
        >
          暂无项目
        </option>
        <option
          v-for="project in workspaceStore.projects"
          :key="project.id"
          :value="project.id"
        >
          {{ project.name }}
        </option>
      </select>
      <BaseIcon
        name="chevron-down"
        size="sm"
        class="pointer-events-none absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 dark:text-dark-400"
      />
    </div>
  </label>
</template>
