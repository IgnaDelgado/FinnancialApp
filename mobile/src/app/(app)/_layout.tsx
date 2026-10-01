import { Redirect, Tabs } from 'expo-router';
import { CalendarDays, ChartNoAxesCombined, Target, UserRound, WalletCards } from 'lucide-react-native';

import { useAuth } from '@/auth/AuthProvider';
import { colors, fontFamily } from '@/theme';

export default function PrivateLayout() {
  const { isBootstrapping, session } = useAuth();
  if (!isBootstrapping && !session) return <Redirect href="/(auth)/login" />;
  return (
    <Tabs screenOptions={{
      headerShown: false,
      tabBarActiveTintColor: colors.forest,
      tabBarInactiveTintColor: colors.muted,
      tabBarLabelStyle: { fontFamily: fontFamily.semibold, fontSize: 10 },
      tabBarStyle: { backgroundColor: colors.white, borderTopColor: colors.line, paddingTop: 5 },
    }}>
      <Tabs.Screen name="index" options={{ title: 'Cuentas', tabBarIcon: ({ color, size }) => <WalletCards color={color} size={size} /> }} />
      <Tabs.Screen name="month" options={{ title: 'Mes', tabBarIcon: ({ color, size }) => <CalendarDays color={color} size={size} /> }} />
      <Tabs.Screen name="goals" options={{ title: 'Objetivos', tabBarIcon: ({ color, size }) => <Target color={color} size={size} /> }} />
      <Tabs.Screen name="investments" options={{ title: 'Inversiones', tabBarIcon: ({ color, size }) => <ChartNoAxesCombined color={color} size={size} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Perfil', tabBarIcon: ({ color, size }) => <UserRound color={color} size={size} /> }} />
      <Tabs.Screen name="accounts" options={{ href: null }} />
    </Tabs>
  );
}
