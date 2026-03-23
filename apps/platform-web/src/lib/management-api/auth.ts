import { requestManagementJson } from "./common";

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    is_super_admin: boolean;
  };
};

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  return requestManagementJson<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: {
  old_password: string;
  new_password: string;
}): Promise<{ ok: boolean }> {
  return requestManagementJson<{ ok: boolean }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
