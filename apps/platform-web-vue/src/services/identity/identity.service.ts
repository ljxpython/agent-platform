import { platformV2HttpClient } from '@/services/http/client'
import type { ManagementUser } from '@/types/management'

export type IdentityServiceMode = 'legacy' | 'runtime'

type IdentityServiceOptions = {
  mode?: IdentityServiceMode
}

type RuntimeUserProfile = {
  id: string
  username: string
  email?: string | null
  status: string
  platform_roles?: string[]
}

function normalizeIdentityUserProfile(
  payload: RuntimeUserProfile | ManagementUser
): ManagementUser {
  if ('is_super_admin' in payload) {
    return payload
  }

  return {
    id: payload.id,
    username: payload.username,
    email: payload.email ?? null,
    status: payload.status,
    is_super_admin: Array.isArray(payload.platform_roles)
      ? payload.platform_roles.includes('platform_super_admin')
      : false
  }
}

export async function getCurrentProfile(
  _requestOptions?: IdentityServiceOptions
): Promise<ManagementUser> {
  const response = await platformV2HttpClient.get('/api/identity/me')
  return normalizeIdentityUserProfile(response.data as RuntimeUserProfile | ManagementUser)
}

export async function updateCurrentProfile(
  payload: {
    username?: string
    email?: string
  },
  _requestOptions?: IdentityServiceOptions
): Promise<ManagementUser> {
  const response = await platformV2HttpClient.patch('/api/identity/me', {
    username: payload.username?.trim() || undefined,
    email: payload.email?.trim() || ''
  })
  return normalizeIdentityUserProfile(response.data as RuntimeUserProfile | ManagementUser)
}

export async function changeCurrentPassword(
  payload: {
    oldPassword: string
    newPassword: string
  },
  _requestOptions?: IdentityServiceOptions
): Promise<{ ok: boolean }> {
  const response = await platformV2HttpClient.post('/api/identity/password/change', {
    old_password: payload.oldPassword,
    new_password: payload.newPassword
  })
  return response.data as { ok: boolean }
}
