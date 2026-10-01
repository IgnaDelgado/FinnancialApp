import { Redirect, Tabs } from 'expo-router';
import { CalendarDays, House, UserRound } from 'lucide-react-native';

import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useAuth } from '@/auth/AuthProvider';
import { colors, fontFamily } from '@/theme';

export default function PrivateLayout() {
  const insets = useSafeAreaInsets();
  const { isBootstrapping, session } = useAuth();
  if (!isBootstrapping && !session) return <Redirect href="/(auth)/login" />;
  return (
    <Tabs screenOptions={{
      headerShown: false,
      tabBarActiveTintColor: colors.forest,
      tabBarInactiveTintColor: colors.muted,
      tabBarLabelStyle: { fontFamily: fontFamily.semibold, fontSize: 11, lineHeight: 16 },
      tabBarStyle: { backgroundColor: colors.white, borderTopColor: colors.line, paddingTop: 8, paddingBottom: Math.max(insets.bottom, 10), height: 80 + insets.bottom },
    }}>
      <Tabs.Screen name="index" options={{ title: 'Inicio', tabBarIcon: ({ color, size }) => <House color={color} size={size} /> }} />
      <Tabs.Screen name="month" options={{ title: 'Mi plan', tabBarIcon: ({ color, size }) => <CalendarDays color={color} size={size} /> }} />
      <Tabs.Screen name="goals" options={{ href: null }} />
      <Tabs.Screen name="investments" options={{ href: null }} />
      <Tabs.Screen name="profile" options={{ title: 'Perfil', tabBarIcon: ({ color, size }) => <UserRound color={color} size={size} /> }} />
      <Tabs.Screen name="accounts" options={{ href: null }} />
    </Tabs>
  );
}
