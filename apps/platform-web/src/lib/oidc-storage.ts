const OIDC_TOKEN_SET_STORAGE_KEY = "platform:oidcTokenSet";
const API_KEY_STORAGE_KEY = "lg:chat:apiKey";
const API_URL_STORAGE_KEY = "lg:chat:apiUrl";

export type OidcTokenSet = {
  access_token?: string;
  refresh_token?: string;
};

function readTokenSet(): OidcTokenSet | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(OIDC_TOKEN_SET_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as OidcTokenSet;
  } catch {
    window.localStorage.removeItem(OIDC_TOKEN_SET_STORAGE_KEY);
    return null;
  }
}

export function getOidcTokenSet(): OidcTokenSet | null {
  return readTokenSet();
}

export function setOidcTokenSet(tokenSet: OidcTokenSet) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(OIDC_TOKEN_SET_STORAGE_KEY, JSON.stringify(tokenSet));
  if (tokenSet.access_token) {
    window.localStorage.setItem(API_KEY_STORAGE_KEY, tokenSet.access_token);
  }
}

export function clearOidcTokenSet() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(OIDC_TOKEN_SET_STORAGE_KEY);
  window.localStorage.removeItem(API_KEY_STORAGE_KEY);
}

export function getValidAccessToken(): string | null {
  const tokenSet = readTokenSet();
  const token = tokenSet?.access_token?.trim();
  return token ? token : null;
}

export function ensureApiUrlSeeded() {
  if (typeof window === "undefined") {
    return;
  }

  const existing = window.localStorage.getItem(API_URL_STORAGE_KEY)?.trim();
  if (existing) {
    return;
  }

  const envApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (envApiUrl) {
    window.localStorage.setItem(API_URL_STORAGE_KEY, envApiUrl);
  }
}
