<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseIcon from '@/components/base/BaseIcon.vue'

const { t } = useI18n()

const isOpen = ref(false)
const rootRef = ref<HTMLElement | null>(null)

function close() {
  isOpen.value = false
}

function toggle() {
  isOpen.value = !isOpen.value
}

function handleClickOutside(event: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(event.target as Node)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div
    ref="rootRef"
    class="relative"
  >
    <button
      type="button"
      class="pw-topbar-action"
      :aria-label="t('topbar.announcements')"
      @click="toggle"
    >
      <span class="relative flex items-center justify-center">
        <BaseIcon
          name="bell"
          size="sm"
        />
        <span class="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-sky-400 ring-2 ring-white dark:ring-dark-900" />
      </span>
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="translate-y-1 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-120 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-1 opacity-0"
    >
      <div
        v-if="isOpen"
        class="pw-topbar-dropdown right-0 mt-3 w-[320px] p-0"
      >
        <div class="border-b border-gray-100 px-4 py-3 dark:border-dark-800">
          <div class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ t('topbar.announcements') }}
          </div>
          <div class="mt-1 text-xs text-gray-500 dark:text-dark-400">
            {{ t('topbar.noUnread') }}
          </div>
        </div>
        <div class="px-4 py-5">
          <div class="rounded-2xl border border-dashed border-gray-200 bg-gray-50/80 px-4 py-5 dark:border-dark-700 dark:bg-dark-900/60">
            <div class="flex items-start gap-3">
              <div class="mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-50 text-sky-500 dark:bg-sky-950/30 dark:text-sky-300">
                <BaseIcon
                  name="info"
                  size="sm"
                />
              </div>
              <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-white">
                  {{ t('topbar.announcementsEmptyTitle') }}
                </div>
                <p class="mt-1 text-sm leading-6 text-gray-500 dark:text-dark-300">
                  {{ t('topbar.announcementsEmptyDescription') }}
                </p>
              </div>
            </div>
          </div>
          <p class="mt-3 text-xs text-gray-400 dark:text-dark-500">
            {{ t('topbar.moreSoon') }}
          </p>
        </div>
      </div>
    </Transition>
  </div>
</template>
