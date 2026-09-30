import { LogOut, RefreshCw, UserRound } from 'lucide-react-native';
import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import { NoticeBanner } from '@/components/NoticeBanner';
import { colors, fontFamily } from '@/theme';

type Action = 'refresh' | 'logout' | 'logout-all' | null;

export default function ProfileScreen() {
  const { refreshProfile, session, signOut, signOutAll } = useAuth();
  const [action, setAction] = useState<Action>(null);
  const [error, setError] = useState<string | null>(null);

  if (!session) return null;

  async function runAction(nextAction: Exclude<Action, null>, operation: () => Promise<void>) {
    setAction(nextAction);
    setError(null);
    try {
      await operation();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'No pudimos completar la acción.');
    } finally {
      setAction(null);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.icon}><UserRound color={colors.forest} size={26} /></View>
        <Text style={styles.title}>Perfil</Text>
        <Text style={styles.intro}>Tus datos y sesiones de acceso.</Text>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Tus datos</Text>
          <Pressable
            accessibilityLabel="Actualizar perfil"
            accessibilityRole="button"
            disabled={action !== null}
            onPress={() => void runAction('refresh', refreshProfile)}
            style={styles.refreshButton}
          >
            {action === 'refresh' ? <ActivityIndicator color={colors.green} size="small" /> : <RefreshCw color={colors.green} size={17} />}
          </Pressable>
        </View>
        <View style={styles.profileCard}>
          <ProfileRow label="Correo" value={session.user.email} />
          <View style={styles.rowDivider} />
          <ProfileRow label="Moneda de referencia" value={session.user.reference_currency} />
          <View style={styles.rowDivider} />
          <ProfileRow label="Te sumaste el" value={formatDate(session.user.created_at)} />
        </View>

        {error ? <NoticeBanner message={error} /> : null}

        <Pressable
          accessibilityRole="button"
          disabled={action !== null}
          onPress={() => void runAction('logout', signOut)}
          style={styles.logoutButton}
        >
          {action === 'logout' ? <ActivityIndicator color={colors.ink} /> : <LogOut color={colors.ink} size={18} />}
          <Text style={styles.logoutText}>Cerrar sesión en este dispositivo</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          disabled={action !== null}
          onPress={() => void runAction('logout-all', signOutAll)}
          style={styles.logoutAllButton}
        >
          <Text style={styles.logoutAllText}>Cerrar todas las sesiones</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.profileRow}>
      <Text style={styles.profileLabel}>{label}</Text>
      <Text style={styles.profileValue}>{value}</Text>
    </View>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'No disponible';
  return new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: 'long', year: 'numeric' }).format(date);
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  content: { paddingBottom: 34, paddingHorizontal: 20, paddingTop: 28 },
  icon: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 20, height: 58, justifyContent: 'center', width: 58 },
  title: { color: colors.ink, fontFamily: fontFamily.displayBold, fontSize: 32, marginTop: 20 },
  intro: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 14, marginTop: 5 },
  sectionHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginTop: 32 },
  sectionTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 21 },
  refreshButton: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 18, borderWidth: 1, height: 38, justifyContent: 'center', width: 38 },
  profileCard: { backgroundColor: colors.white, borderColor: colors.line, borderRadius: 22, borderWidth: 1, marginTop: 12, paddingHorizontal: 16 },
  profileRow: { alignItems: 'center', flexDirection: 'row', gap: 14, minHeight: 58 },
  profileLabel: { color: colors.muted, flex: 1, fontFamily: fontFamily.body, fontSize: 12 },
  profileValue: { color: colors.ink, flex: 1.5, fontFamily: fontFamily.semibold, fontSize: 12, textAlign: 'right' },
  rowDivider: { backgroundColor: colors.line, height: 1 },
  logoutButton: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 17, borderWidth: 1, flexDirection: 'row', gap: 9, justifyContent: 'center', marginTop: 24, minHeight: 54 },
  logoutText: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 12 },
  logoutAllButton: { alignItems: 'center', justifyContent: 'center', minHeight: 50 },
  logoutAllText: { color: colors.coral, fontFamily: fontFamily.semibold, fontSize: 11 },
});
