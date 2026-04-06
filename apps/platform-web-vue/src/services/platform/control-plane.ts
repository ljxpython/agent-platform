import { getAccessToken } from '@/services/auth/token'
import {
  httpClient,
  platformV2HttpClient
} from '@/services/http/client'

export type PlatformClientModule =
  | 'system'
  | 'identity'
  | 'projects'
  | 'members'
  | 'users'
  | 'announcements'
  | 'audit'
  | 'operations'
  | 'assistants'
  | 'testcase'
  | 'runtime_catalog'
  | 'runtime_gateway'

export type PlatformClientScope = 'legacy' | 'v2'

export function resolvePlatformClientScope(_module: PlatformClientModule): PlatformClientScope {
  return 'v2'
}

export function getPlatformHttpClient(_module: PlatformClientModule) {
  return platformV2HttpClient
}

export function getPlatformApiBaseUrl(_module: PlatformClientModule): string {
  return httpClient.defaults.baseURL || ''
}

export function getPlatformAccessToken(_module: PlatformClientModule): string {
  return getAccessToken()
}
