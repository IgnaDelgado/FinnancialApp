import {
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  LogOut,
  RefreshCw,
  ShieldCheck,
  UserRound,
  WalletCards,
} from 'lucide-react-native';
import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import { BrandMark } from '@/components/BrandMark';
import { NoticeBanner } from '@/components/NoticeBanner';
import { colors, fontFamily } from '@/theme';

type Action = 'profile' | 'logout' | 'logout-all' | null;

export default function HomeScreen() {
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
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topBar}>
          <BrandMark />
          <View style={styles.avatar}>
            <UserRound color={colors.forest} size={20} />
          </View>
        </View>

        <Text style={styles.eyebrow}>TU ESPACIO FINANCIERO</Text>
        <Text style={styles.greeting}>Todo listo para empezar.</Text>
        <Text style={styles.intro}>
          Tu cuenta está protegida. El próximo paso es registrar dónde está tu dinero.
        </Text>

        <View style={styles.heroCard}>
          <View style={styles.heroTop}>
            <View style={styles.heroIcon}>
              <WalletCards color={colors.forestDeep} size={22} />
            </View>
            <View style={styles.readyBadge}>
              <CheckCircle2 color={colors.mint} size={14} />
              <Text style={styles.readyText}>CUENTA ACTIVA</Text>
            </View>
          </View>
          <Text style={styles.heroLabel}>DINERO DISPONIBLE</Text>
          <Text style={styles.heroValue}>Agregá tu primera cuenta</Text>
          <Text style={styles.heroDescription}>
            Todavía no mostramos un monto porque no hay balances registrados. Así evitamos inventar o duplicar dinero.
          </Text>
          <View style={styles.heroDivider} />
          <View style={styles.heroFooter}>
            <Text style={styles.heroFooterLabel}>MONEDA DE REFERENCIA</Text>
            <Text style={styles.heroCurrency}>{session.user.reference_currency}</Text>
          </View>
        </View>

        <View style={styles.nextCard}>
          <View style={styles.stepNumber}><Text style={styles.stepNumberText}>01</Text></View>
          <View style={styles.nextCopy}>
            <Text style={styles.nextTitle}>Crear una cuenta financiera</Text>
            <Text style={styles.nextDescription}>Efectivo, banco o billetera digital.</Text>
          </View>
          <ChevronRight color={colors.muted} size={19} />
        </View>
        <Text style={styles.comingSoon}>Disponible en el siguiente módulo del roadmap.</Text>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Tu perfil</Text>
          <Pressable
            accessibilityLabel="Actualizar perfil"
            disabled={action !== null}
            onPress={() => void runAction('profile', refreshProfile)}
            style={styles.refreshButton}
          >
            {action === 'profile' ? (
              <ActivityIndicator color={colors.green} size="small" />
            ) : (
              <RefreshCw color={colors.green} size={17} />
            )}
          </Pressable>
        </View>

        <View style={styles.profileCard}>
          <ProfileRow label="Correo" value={session.user.email} />
          <View style={styles.rowDivider} />
          <ProfileRow label="Moneda de referencia" value={session.user.reference_currency} />
          <View style={styles.rowDivider} />
          <ProfileRow label="Cuenta creada" value={formatDate(session.user.created_at)} />
        </View>

        <View style={styles.securityCard}>
          <ShieldCheck color={colors.green} size={21} />
          <View style={styles.securityCopy}>
            <Text style={styles.securityTitle}>Sesión protegida</Text>
            <Text style={styles.securityDescription}>
              El acceso corto vive en memoria y la credencial de renovación se guarda cifrada en el dispositivo.
            </Text>
          </View>
        </View>

        {error ? <NoticeBanner message={error} /> : null}

        <Pressable
          disabled={action !== null}
          onPress={() => void runAction('logout', signOut)}
          style={({ pressed }) => [styles.logoutButton, pressed && styles.pressed]}
        >
          {action === 'logout' ? <ActivityIndicator color={colors.ink} /> : <LogOut color={colors.ink} size={18} />}
          <Text style={styles.logoutText}>Cerrar sesión en este dispositivo</Text>
        </Pressable>
        <Pressable
          disabled={action !== null}
          onPress={() => void runAction('logout-all', signOutAll)}
          style={styles.logoutAllButton}
        >
          <ArrowUpRight color={colors.coral} size={16} />
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
      <Text numberOfLines={1} style={styles.profileValue}>{value}</Text>
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
  content: { paddingBottom: 34, paddingHorizontal: 22 },
  topBar: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', paddingTop: 12 },
  avatar: { alignItems: 'center', backgroundColor: colors.softMint, borderRadius: 22, height: 43, justifyContent: 'center', width: 43 },
  eyebrow: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 10, letterSpacing: 1.15, marginTop: 36 },
  greeting: { color: colors.ink, fontFamily: fontFamily.displayBold, fontSize: 33, letterSpacing: -0.8, lineHeight: 38, marginTop: 6 },
  intro: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 14, lineHeight: 21, marginTop: 7, maxWidth: 335 },
  heroCard: { backgroundColor: colors.forestDeep, borderRadius: 24, marginTop: 24, padding: 20 },
  heroTop: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  heroIcon: { alignItems: 'center', backgroundColor: colors.mint, borderRadius: 12, height: 43, justifyContent: 'center', width: 43 },
  readyBadge: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 20, flexDirection: 'row', gap: 6, paddingHorizontal: 10, paddingVertical: 7 },
  readyText: { color: colors.mint, fontFamily: fontFamily.bold, fontSize: 9, letterSpacing: 0.65 },
  heroLabel: { color: '#AFC2BA', fontFamily: fontFamily.bold, fontSize: 9, letterSpacing: 0.8, marginTop: 27 },
  heroValue: { color: colors.white, fontFamily: fontFamily.displayMedium, fontSize: 23, marginTop: 5 },
  heroDescription: { color: '#BFCFC9', fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18, marginTop: 7 },
  heroDivider: { backgroundColor: 'rgba(255,255,255,0.1)', height: 1, marginVertical: 18 },
  heroFooter: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  heroFooterLabel: { color: '#AFC2BA', fontFamily: fontFamily.bold, fontSize: 9, letterSpacing: 0.65 },
  heroCurrency: { color: colors.mint, fontFamily: fontFamily.bold, fontSize: 14 },
  nextCard: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 18, borderWidth: 1, flexDirection: 'row', gap: 12, marginTop: 18, padding: 14 },
  stepNumber: { alignItems: 'center', backgroundColor: colors.paleYellow, borderRadius: 11, height: 42, justifyContent: 'center', width: 42 },
  stepNumberText: { color: '#78672E', fontFamily: fontFamily.bold, fontSize: 12 },
  nextCopy: { flex: 1 },
  nextTitle: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  nextDescription: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 11, marginTop: 3 },
  comingSoon: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 10, marginLeft: 4, marginTop: 7 },
  sectionHeader: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginTop: 29 },
  sectionTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 21 },
  refreshButton: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 18, height: 35, justifyContent: 'center', width: 35 },
  profileCard: { backgroundColor: colors.white, borderColor: colors.line, borderRadius: 18, borderWidth: 1, marginTop: 11, paddingHorizontal: 15 },
  profileRow: { alignItems: 'center', flexDirection: 'row', gap: 14, minHeight: 51 },
  profileLabel: { color: colors.muted, flex: 1, fontFamily: fontFamily.body, fontSize: 12 },
  profileValue: { color: colors.ink, flex: 1.5, fontFamily: fontFamily.semibold, fontSize: 12, textAlign: 'right' },
  rowDivider: { backgroundColor: colors.line, height: 1 },
  securityCard: { alignItems: 'flex-start', backgroundColor: colors.paleGreen, borderRadius: 16, flexDirection: 'row', gap: 11, marginBottom: 18, marginTop: 16, padding: 14 },
  securityCopy: { flex: 1 },
  securityTitle: { color: colors.forest, fontFamily: fontFamily.bold, fontSize: 12 },
  securityDescription: { color: colors.green, fontFamily: fontFamily.body, fontSize: 10, lineHeight: 15, marginTop: 3 },
  logoutButton: { alignItems: 'center', borderColor: colors.line, borderRadius: 14, borderWidth: 1, flexDirection: 'row', gap: 9, justifyContent: 'center', marginTop: 18, minHeight: 51 },
  logoutText: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 12 },
  logoutAllButton: { alignItems: 'center', flexDirection: 'row', gap: 7, justifyContent: 'center', minHeight: 45 },
  logoutAllText: { color: colors.coral, fontFamily: fontFamily.semibold, fontSize: 11 },
  pressed: { backgroundColor: '#E9ECE6' },
});
