export async function completeGlobalSignOut(
  revokeSessions: () => Promise<void>,
  clearToken: () => Promise<void>,
  clearSession: () => void,
): Promise<void> {
  await revokeSessions();
  try {
    await clearToken();
  } finally {
    clearSession();
  }
}
