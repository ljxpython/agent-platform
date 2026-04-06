import { platformV2HttpClient } from '@/services/http/client'
import type { ManagementProject, ManagementProjectListResponse } from '@/types/management'

export type ProjectServiceMode = 'legacy' | 'runtime'

type ProjectServiceOptions = {
  mode?: ProjectServiceMode
}

export async function listProjectsPage(options?: {
  limit?: number
  offset?: number
  query?: string
}, _requestOptions?: ProjectServiceOptions): Promise<ManagementProjectListResponse> {
  const response = await platformV2HttpClient.get('/api/projects', {
    params: {
      limit: options?.limit ?? 100,
      offset: options?.offset ?? 0,
      query: options?.query?.trim() || undefined
    }
  })

  return response.data as ManagementProjectListResponse
}

export async function listProjects(
  requestOptions?: ProjectServiceOptions
): Promise<ManagementProject[]> {
  const payload = await listProjectsPage(undefined, requestOptions)
  return payload.items
}

export async function listRuntimeProjectsPage(options?: {
  limit?: number
  offset?: number
  query?: string
}): Promise<ManagementProjectListResponse> {
  return listProjectsPage(options, { mode: 'runtime' })
}

export async function listRuntimeProjects(): Promise<ManagementProject[]> {
  return listProjects({ mode: 'runtime' })
}

export async function createProject(payload: {
  name: string
  description?: string
}, _requestOptions?: ProjectServiceOptions): Promise<ManagementProject> {
  const response = await platformV2HttpClient.post('/api/projects', payload)
  return response.data as ManagementProject
}

export async function createRuntimeProject(payload: {
  name: string
  description?: string
}): Promise<ManagementProject> {
  return createProject(payload, { mode: 'runtime' })
}
