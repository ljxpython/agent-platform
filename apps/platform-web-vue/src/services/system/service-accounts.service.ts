import { platformV2HttpClient } from '@/services/http/client'
import type {
  CreatedServiceAccountToken,
  ManagementServiceAccount,
  ManagementServiceAccountPage
} from '@/types/management'

export async function listServiceAccounts(options?: {
  limit?: number
  offset?: number
  query?: string
  status?: string
}): Promise<ManagementServiceAccountPage> {
  const response = await platformV2HttpClient.get('/api/service-accounts', {
    params: {
      limit: options?.limit ?? 50,
      offset: options?.offset ?? 0,
      query: options?.query?.trim() || undefined,
      status: options?.status?.trim() || undefined
    }
  })
  return response.data as ManagementServiceAccountPage
}

export async function createServiceAccount(payload: {
  name: string
  description?: string
  platform_roles: string[]
}): Promise<ManagementServiceAccount> {
  const response = await platformV2HttpClient.post('/api/service-accounts', payload)
  return response.data as ManagementServiceAccount
}

export async function updateServiceAccount(
  serviceAccountId: string,
  payload: {
    description?: string | null
    status?: 'active' | 'disabled'
    platform_roles?: string[]
  }
): Promise<ManagementServiceAccount> {
  const response = await platformV2HttpClient.patch(`/api/service-accounts/${serviceAccountId}`, payload)
  return response.data as ManagementServiceAccount
}

export async function createServiceAccountToken(
  serviceAccountId: string,
  payload: {
    name: string
    expires_in_days?: number
  }
): Promise<CreatedServiceAccountToken> {
  const response = await platformV2HttpClient.post(
    `/api/service-accounts/${serviceAccountId}/tokens`,
    payload
  )
  return response.data as CreatedServiceAccountToken
}

export async function revokeServiceAccountToken(
  serviceAccountId: string,
  tokenId: string
): Promise<void> {
  await platformV2HttpClient.delete(`/api/service-accounts/${serviceAccountId}/tokens/${tokenId}`)
}

