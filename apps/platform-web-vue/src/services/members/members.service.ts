import { platformV2HttpClient } from '@/services/http/client'
import type { ManagementProjectMember } from '@/types/management'

type MemberListResponse = {
  items: ManagementProjectMember[]
}

export type MemberServiceMode = 'legacy' | 'runtime'

type MemberServiceOptions = {
  mode?: MemberServiceMode
}

export async function listProjectMembers(
  projectId: string,
  options?: { query?: string },
  _requestOptions?: MemberServiceOptions
): Promise<ManagementProjectMember[]> {
  if (!projectId) {
    return []
  }

  const response = await platformV2HttpClient.get(`/api/projects/${projectId}/members`, {
    params: {
      query: options?.query?.trim() || undefined
    }
  })

  const payload = response.data as MemberListResponse
  return Array.isArray(payload.items) ? payload.items : []
}

export async function upsertProjectMember(payload: {
  projectId: string
  userId: string
  role: 'admin' | 'editor' | 'executor'
}, _requestOptions?: MemberServiceOptions): Promise<ManagementProjectMember> {
  const response = await platformV2HttpClient.put(
    `/api/projects/${payload.projectId}/members/${payload.userId}`,
    {
      role: payload.role
    }
  )

  return response.data as ManagementProjectMember
}

export async function deleteProjectMember(
  projectId: string,
  userId: string,
  _requestOptions?: MemberServiceOptions
): Promise<{ ok: boolean }> {
  const response = await platformV2HttpClient.delete(`/api/projects/${projectId}/members/${userId}`)

  return response.data as { ok: boolean }
}
