import { defineStore } from 'pinia'
import { listProjects } from '@/services/projects/projects.service'
import type { ManagementProject } from '@/types/management'

const PROJECT_STORAGE_KEY = 'pw:workspace:project-id'

function readProjectPreference(storageKey: string) {
  if (typeof window === 'undefined') {
    return ''
  }

  return window.localStorage.getItem(storageKey)?.trim() || ''
}

function writeProjectPreference(storageKey: string, projectId: string) {
  if (typeof window === 'undefined') {
    return
  }

  if (projectId) {
    window.localStorage.setItem(storageKey, projectId)
    return
  }

  window.localStorage.removeItem(storageKey)
}

export const useWorkspaceStore = defineStore('workspace', {
  state: () => ({
    currentProjectId: '',
    projects: [] as ManagementProject[],
    loading: false,
    runtimeProjectId: '',
    runtimeProjects: [] as ManagementProject[],
    runtimeLoading: false
  }),
  getters: {
    currentProject(state) {
      return state.projects.find((project) => project.id === state.currentProjectId) ?? null
    },
    runtimeProject(state) {
      return state.projects.find((project) => project.id === state.currentProjectId) ?? null
    },
    runtimeScope() {
      return 'v2'
    },
    runtimeContextEnabled() {
      return true
    },
    runtimeScopedProjectId(state) {
      return state.currentProjectId
    },
    runtimeScopedProjects(state) {
      return state.projects
    },
    runtimeScopedProject(state) {
      return state.projects.find((project) => project.id === state.currentProjectId) ?? null
    }
  },
  actions: {
    hydrateProjectPreference() {
      this.currentProjectId = readProjectPreference(PROJECT_STORAGE_KEY)
      this.runtimeProjectId = this.currentProjectId
    },
    setProjectId(projectId: string) {
      this.currentProjectId = projectId
      this.runtimeProjectId = projectId
      writeProjectPreference(PROJECT_STORAGE_KEY, projectId)
    },
    setRuntimeProjectId(projectId: string) {
      this.setProjectId(projectId)
    },
    async hydrateContext() {
      this.loading = true

      try {
        this.hydrateProjectPreference()
        const rows = await listProjects()
        this.projects = rows
        this.runtimeProjects = rows

        const nextProjectId =
          rows.find((project) => project.id === this.currentProjectId)?.id ||
          rows[0]?.id ||
          ''

        this.setProjectId(nextProjectId)
      } catch {
        this.projects = []
        this.setProjectId('')
      } finally {
        this.loading = false
      }
    },
    async hydrateRuntimeContext() {
      this.runtimeLoading = true
      try {
        await this.hydrateContext()
      } finally {
        this.runtimeLoading = false
      }
    },
    reset() {
      this.projects = []
      this.setProjectId('')
      this.runtimeProjects = []
      this.runtimeProjectId = ''
      this.loading = false
      this.runtimeLoading = false
    }
  }
})
