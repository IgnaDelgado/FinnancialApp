import { LinearGradient } from 'expo-linear-gradient';
import { Link, useFocusEffect } from 'expo-router';
import {
  ChevronRight,
  LogOut,
  RefreshCw,
  UserRound,
  WalletCards,
} from 'lucide-react-native';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AccessibilityInfo,
  ActivityIndicator,
  Animated,
  Easing,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import {
  getAccountCashTotals,
  listAccounts,
  type AccountCashTotal,
  type FinancialAccount,
} from '@/accounts/api';
import { formatMoney } from '@/accounts/format';
import { BrandMark } from '@/components/BrandMark';
import { NoticeBanner } from '@/components/NoticeBanner';
import { colors, fontFamily } from '@/theme';

type Action = 'profile' | 'logout' | 'logout-all' | null;

export default function HomeScreen() {
  const { refreshProfile, session, signOut, signOutAll, withAccessToken } = useAuth();
  const [accounts, setAccounts] = useState<FinancialAccount[] | null>(null);
  const [cashTotals, setCashTotals] = useState<AccountCashTotal[]>([]);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const [action, setAction] = useState<Action>(null);
  const [error, setError] = useState<string | null>(null);
  const entrance = useMemo(() => new Animated.Value(0), []);

  useFocusEffect(useCallback(() => {
    if (!session) return;
    let active = true;
    setAccounts(null);
    setCashTotals([]);
    setAccountsError(null);
    void withAccessToken((token) => Promise.all([listAccounts(token), getAccountCashTotals(token)]))
      .then(([accountResult, totalResult]) => {
        if (!active) return;
        setAccounts(accountResult);
        setCashTotals(totalResult);
        setAccountsError(null);
      })
      .catch((caught) => {
        if (active) setAccountsError(caught instanceof ApiError ? caught.message : 'No pudimos cargar tus cuentas.');
      });
    return () => { active = false; };
  }, [session, withAccessToken]));

  useEffect(() => {
    let active = true;
    void AccessibilityInfo.isReduceMotionEnabled().then((reduceMotion) => {
      if (!active) return;
      if (reduceMotion) {
        entrance.setValue(1);
        return;
      }
      Animated.timing(entrance, {
        duration: 650,
        easing: Easing.out(Easing.cubic),
        toValue: 1,
        useNativeDriver: true,
      }).start();
    });
    return () => {
      active = false;
    };
  }, [entrance]);

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

  const translateY = entrance.interpolate({ inputRange: [0, 1], outputRange: [22, 0] });
  const opacity = entrance.interpolate({ inputRange: [0, 1], outputRange: [0.32, 1] });

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <LinearGradient colors={['#FFF9F3', '#F5FAF7', '#F3F3FF']} style={styles.flex}>
        <View pointerEvents="none" style={styles.backgroundMint} />
        <View pointerEvents="none" style={styles.backgroundPeach} />
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <Animated.View style={{ opacity, transform: [{ translateY }] }}>
            <View style={styles.topBar}>
              <BrandMark />
              <View style={styles.avatar}>
                <UserRound color={colors.forest} size={19} />
              </View>
            </View>

            <Text style={styles.greeting}>Tus cuentas, en claro.</Text>
            <Text style={styles.intro}>
              Por ahora, este inicio muestra tus saldos registrados. El dinero disponible y el patrimonio neto llegarán cuando incorporemos el resto del plan.
            </Text>

            <LinearGradient
              colors={['#DDF5EB', '#EFF0FF']}
              end={{ x: 1, y: 1 }}
              start={{ x: 0, y: 0 }}
              style={styles.heroCard}
            >
              <View style={styles.heroTop}>
                <View style={styles.heroIcon}>
                  <WalletCards color={colors.forest} size={24} />
                </View>
                <Text style={styles.heroLabel}>SALDO TOTAL DE CUENTAS</Text>
              </View>
              {accountsError ? (
                <Text style={styles.heroValue}>No pudimos mostrar tus saldos</Text>
              ) : accounts === null ? (
                <ActivityIndicator color={colors.forest} style={styles.accountsLoading} />
              ) : accounts?.length ? (
                cashTotals.map((total) => (
                  <Text
                    key={total.currency}
                    style={[styles.heroValue, total.balance.startsWith('-') && styles.negativeBalance]}
                  >
                    {formatMoney(total.balance, total.currency)}
                  </Text>
                ))
              ) : (
                <Text style={styles.heroValue}>Todavía no registraste cuentas</Text>
              )}
              <Text style={styles.heroDescription}>Suma saldos positivos y negativos por moneda. No es dinero disponible para gastar.</Text>
              <View style={styles.heroFooter}>
                <Text style={styles.heroFooterLabel}>ACTUALIZÁ TUS SALDOS CUANDO CAMBIEN</Text>
                <Link href="/accounts" asChild>
                  <Pressable accessibilityRole="button" style={styles.futureButton}>
                    <Text style={styles.futureButtonText}>{accounts?.length ? 'GESTIONAR' : 'AGREGAR'}</Text>
                    <ChevronRight color={colors.lavenderDeep} size={16} />
                  </Pressable>
                </Link>
              </View>
            </LinearGradient>

            {accountsError ? <NoticeBanner message={accountsError} /> : null}

            {accounts?.length ? (
              <View style={styles.accountList}>
                <Text style={styles.sectionTitle}>Tus cuentas</Text>
                {accounts.map((account) => (
                  <Link href="/accounts" asChild key={account.id}>
                    <Pressable style={styles.accountRow}>
                      <View style={styles.accountRowCopy}>
                        <Text style={styles.accountName}>{account.name}</Text>
                        <Text style={styles.accountMeta}>{account.current_balance.startsWith('-') ? 'Saldo en rojo' : account.is_liquid ? 'Cuenta líquida' : 'No líquida'}</Text>
                      </View>
                      <Text style={[styles.accountBalance, account.current_balance.startsWith('-') && styles.negativeBalance]}>{formatMoney(account.current_balance, account.currency)}</Text>
                      <ChevronRight color={colors.muted} size={15} />
                    </Pressable>
                  </Link>
                ))}
              </View>
            ) : null}

            <View style={styles.sectionHeader}>
              <View>
                <Text style={styles.sectionEyebrow}>TUS DATOS</Text>
                <Text style={styles.sectionTitle}>Perfil</Text>
              </View>
              <Pressable
                accessibilityLabel="Actualizar perfil"
                disabled={action !== null}
                onPress={() => void runAction('profile', refreshProfile)}
                style={({ pressed }) => [styles.refreshButton, pressed && styles.pressed]}
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
              <ProfileRow label="Te sumaste el" value={formatDate(session.user.created_at)} />
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
              style={({ pressed }) => [styles.logoutAllButton, pressed && styles.pressed]}
            >
              <Text style={styles.logoutAllText}>Cerrar todas las sesiones</Text>
            </Pressable>
          </Animated.View>
        </ScrollView>
      </LinearGradient>
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
  flex: { flex: 1 },
  safeArea: { backgroundColor: '#FFF9F3', flex: 1 },
  backgroundMint: { backgroundColor: colors.mintBright, borderRadius: 100, height: 200, opacity: 0.2, position: 'absolute', right: -90, top: 70, width: 200 },
  backgroundPeach: { backgroundColor: colors.peach, borderRadius: 80, height: 160, left: -100, opacity: 0.22, position: 'absolute', top: 430, width: 160 },
  content: { paddingBottom: 34, paddingHorizontal: 20 },
  topBar: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', paddingTop: 12 },
  avatar: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 22, borderWidth: 1, height: 43, justifyContent: 'center', shadowColor: colors.shadow, shadowOffset: { height: 4, width: 0 }, shadowOpacity: 0.08, shadowRadius: 10, width: 43 },
  greeting: { color: colors.ink, fontFamily: fontFamily.displayBold, fontSize: 34, letterSpacing: -1, lineHeight: 39, marginTop: 31 },
  intro: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 14, lineHeight: 21, marginTop: 7, maxWidth: 345 },
  heroCard: { borderColor: 'rgba(255,255,255,0.8)', borderRadius: 28, borderWidth: 1, marginTop: 23, padding: 19, shadowColor: colors.shadow, shadowOffset: { height: 12, width: 0 }, shadowOpacity: 0.09, shadowRadius: 24 },
  heroTop: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  heroIcon: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.72)', borderRadius: 15, height: 49, justifyContent: 'center', width: 49 },
  heroLabel: { color: colors.green, flex: 1, fontFamily: fontFamily.bold, fontSize: 9, letterSpacing: 0.8, textAlign: 'right' },
  heroValue: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 24, letterSpacing: -0.4, marginTop: 5 },
  accountsLoading: { alignSelf: 'flex-start', marginTop: 16 },
  heroDescription: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18, marginTop: 7 },
  heroFooter: { alignItems: 'center', borderTopColor: 'rgba(57,121,107,0.12)', borderTopWidth: 1, flexDirection: 'row', gap: 8, justifyContent: 'space-between', marginTop: 18, paddingTop: 15 },
  heroFooterLabel: { color: colors.muted, flex: 1, fontFamily: fontFamily.bold, fontSize: 8, letterSpacing: 0.65 },
  futureButton: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.68)', borderRadius: 12, flexDirection: 'row', gap: 3, paddingHorizontal: 9, paddingVertical: 8 },
  futureButtonText: { color: colors.lavenderDeep, fontFamily: fontFamily.bold, fontSize: 7.5, letterSpacing: 0.55 },
  accountList: { gap: 9, marginTop: 25 },
  accountRow: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 16, borderWidth: 1, flexDirection: 'row', gap: 8, minHeight: 66, paddingHorizontal: 13 },
  accountRowCopy: { flex: 1, gap: 3 },
  accountName: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  accountMeta: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 10 },
  accountBalance: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 12 },
  negativeBalance: { color: colors.coral },
  sectionHeader: { alignItems: 'flex-end', flexDirection: 'row', justifyContent: 'space-between', marginTop: 30 },
  sectionEyebrow: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 8.5, letterSpacing: 0.8 },
  sectionTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 22, marginTop: 2 },
  refreshButton: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 18, borderWidth: 1, height: 37, justifyContent: 'center', width: 37 },
  profileCard: { backgroundColor: 'rgba(255,255,255,0.9)', borderColor: colors.line, borderRadius: 22, borderWidth: 1, marginTop: 11, paddingHorizontal: 16 },
  profileRow: { alignItems: 'center', flexDirection: 'row', gap: 14, minHeight: 54 },
  profileLabel: { color: colors.muted, flex: 1, fontFamily: fontFamily.body, fontSize: 12 },
  profileValue: { color: colors.ink, flex: 1.55, fontFamily: fontFamily.semibold, fontSize: 12, textAlign: 'right' },
  rowDivider: { backgroundColor: colors.line, height: 1 },
  logoutButton: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.74)', borderColor: colors.line, borderRadius: 17, borderWidth: 1, flexDirection: 'row', gap: 9, justifyContent: 'center', marginTop: 18, minHeight: 54 },
  logoutText: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 12 },
  logoutAllButton: { alignItems: 'center', flexDirection: 'row', gap: 7, justifyContent: 'center', minHeight: 47 },
  logoutAllText: { color: colors.coral, fontFamily: fontFamily.semibold, fontSize: 11 },
  pressed: { opacity: 0.7, transform: [{ scale: 0.985 }] },
});
