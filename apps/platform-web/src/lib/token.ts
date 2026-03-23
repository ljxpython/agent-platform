export function isJwtToken(value: string | null | undefined): value is string {
  if (!value) {
    return false;
  }

  return value.split(".").length === 3;
}
