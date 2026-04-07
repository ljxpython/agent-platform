import { getAccessToken } from '@/services/auth/token'
import {
  platformApiBaseUrl,
  platformHttpClient
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

export function getPlatformHttpClient(_module: PlatformClientModule) {
  return platformHttpClient
}

export function getPlatformApiBaseUrl(_module: PlatformClientModule): string {
  return platformApiBaseUrl
}

export function getPlatformAccessToken(_module: PlatformClientModule): string {
  return getAccessToken()
}
