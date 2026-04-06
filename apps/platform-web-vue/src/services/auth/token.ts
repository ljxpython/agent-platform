import type { AuthTokenSet } from '@/types/management'

const TOKEN_STORAGE_KEY = 'pw:auth:token-set'
export type AuthTokenScope = 'legacy' | 'v2'

function getLegacyStorageKeys(scope?: AuthTokenScope) {
  if (scope === 'v2') {
    return [`${TOKEN_STORAGE_KEY}:v2`]
  }

  if (scope === 'legacy') {
    return [TOKEN_STORAGE_KEY]
  }

  return [TOKEN_STORAGE_KEY, `${TOKEN_STORAGE_KEY}:v2`]
}

function parseTokenSet(raw: string): AuthTokenSet | null {
  try {
    return JSON.parse(raw) as AuthTokenSet
  } catch {
    return null
  }
}

function clearLegacyKeys() {
  if (typeof window === 'undefined') {
    return
  }

  for (const key of [TOKEN_STORAGE_KEY, `${TOKEN_STORAGE_KEY}:v2`]) {
    window.localStorage.removeItem(key)
  }
}

export function getTokenSet(scope: AuthTokenScope = 'legacy'): AuthTokenSet | null {
  if (typeof window === 'undefined') {
    return null
  }

  for (const key of getLegacyStorageKeys(scope)) {
    const raw = window.localStorage.getItem(key)
    if (!raw) {
      continue
    }
    const tokenSet = parseTokenSet(raw)
    if (tokenSet) {
      return tokenSet
    }
  }

  return null
}

export function setTokenSet(tokenSet: AuthTokenSet, _scope: AuthTokenScope = 'legacy'): void {
  if (typeof window === 'undefined') {
    return
  }

  clearLegacyKeys()
  window.localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokenSet))
}

export function clearTokenSet(scope: AuthTokenScope = 'legacy'): void {
  if (typeof window === 'undefined') {
    return
  }

  for (const key of getLegacyStorageKeys(scope)) {
    window.localStorage.removeItem(key)
  }
}

export function clearAllTokenSets(): void {
  clearLegacyKeys()
}

export function getAccessToken(scope: AuthTokenScope = 'legacy'): string {
  return getTokenSet(scope)?.accessToken?.trim() || ''
}

export function getRefreshToken(scope: AuthTokenScope = 'legacy'): string {
  return getTokenSet(scope)?.refreshToken?.trim() || ''
}
