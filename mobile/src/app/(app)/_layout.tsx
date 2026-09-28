import { Redirect, Stack } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';

export default function PrivateLayout() {
  const { isBootstrapping, session } = useAuth();
  if (!isBootstrapping && !session) return <Redirect href="/(auth)/login" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
