<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseIcon from '@/components/base/BaseIcon.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'

const props = withDefaults(
  defineProps<{
    total: number
    page: number
    pageSize: number
    pageSizeOptions?: number[]
    disabled?: boolean
  }>(),
  {
    pageSizeOptions: () => [10, 20, 50, 100],
    disabled: false
  }
)

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
}>()

const { t } = useI18n()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const from = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1))
const to = computed(() => Math.min(props.page * props.pageSize, props.total))

const visiblePages = computed(() => {
  const pages: Array<number | 'ellipsis'> = []
  const maxVisible = 7

  if (totalPages.value <= maxVisible) {
    for (let index = 1; index <= totalPages.value; index += 1) {
      pages.push(index)
    }
    return pages
  }

  pages.push(1)

  const start = Math.max(2, props.page - 1)
  const end = Math.min(totalPages.value - 1, props.page + 1)

  if (start > 2) {
    pages.push('ellipsis')
  }

  for (let index = start; index <= end; index += 1) {
    pages.push(index)
  }

  if (end < totalPages.value - 1) {
    pages.push('ellipsis')
  }

  pages.push(totalPages.value)

  return pages
})

function goToPage(page: number) {
  if (props.disabled) {
    return
  }

  const safePage = Math.min(Math.max(page, 1), totalPages.value)
  if (safePage !== props.page) {
    emit('update:page', safePage)
  }
}

function handlePageSizeChange(value: string) {
  const nextPageSize = Number.parseInt(value, 10)
  if (Number.isFinite(nextPageSize) && nextPageSize > 0) {
    emit('update:pageSize', nextPageSize)
  }
}
</script>

<template>
  <div class="pw-pagination-shell">
    <div class="flex flex-1 items-center justify-between gap-3 sm:hidden">
      <button
        type="button"
        class="pw-pagination-nav"
        :disabled="disabled || page <= 1"
        @click="goToPage(page - 1)"
      >
        {{ t('pagination.previous') }}
      </button>
      <span class="text-sm text-gray-500 dark:text-dark-300">
        {{ t('pagination.pageOf', { page, total: totalPages }) }}
      </span>
      <button
        type="button"
        class="pw-pagination-nav"
        :disabled="disabled || page >= totalPages"
        @click="goToPage(page + 1)"
      >
        {{ t('pagination.next') }}
      </button>
    </div>

    <div class="hidden flex-1 items-center justify-between gap-4 sm:flex">
      <div class="flex items-center gap-4">
        <p class="text-sm text-gray-500 dark:text-dark-300">
          {{ t('pagination.showing') }}
          <span class="font-semibold text-gray-900 dark:text-white">{{ from }}</span>
          {{ t('pagination.to') }}
          <span class="font-semibold text-gray-900 dark:text-white">{{ to }}</span>
          {{ t('pagination.of') }}
          <span class="font-semibold text-gray-900 dark:text-white">{{ total }}</span>
          {{ t('pagination.results') }}
        </p>

        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500 dark:text-dark-300">{{ t('pagination.perPage') }}</span>
          <div class="w-24">
            <BaseSelect
              :model-value="String(pageSize)"
              @update:model-value="handlePageSizeChange"
            >
              <option
                v-for="option in pageSizeOptions"
                :key="option"
                :value="option"
              >
                {{ option }}
              </option>
            </BaseSelect>
          </div>
        </div>
      </div>

      <nav class="flex items-center gap-1">
        <button
          type="button"
          class="pw-pagination-nav"
          :disabled="disabled || page <= 1"
          @click="goToPage(page - 1)"
        >
          <BaseIcon
            name="chevron-left"
            size="sm"
          />
        </button>

        <template
          v-for="(item, index) in visiblePages"
          :key="`${item}-${index}`"
        >
          <span
            v-if="item === 'ellipsis'"
            class="px-2 text-sm text-gray-400 dark:text-dark-400"
          >
            ...
          </span>
          <button
            v-else
            type="button"
            class="pw-pagination-page"
            :class="item === page ? 'pw-pagination-page-active' : ''"
            :disabled="disabled"
            @click="goToPage(item)"
          >
            {{ item }}
          </button>
        </template>

        <button
          type="button"
          class="pw-pagination-nav"
          :disabled="disabled || page >= totalPages"
          @click="goToPage(page + 1)"
        >
          <BaseIcon
            name="chevron-right"
            size="sm"
          />
        </button>
      </nav>
    </div>
  </div>
</template>
