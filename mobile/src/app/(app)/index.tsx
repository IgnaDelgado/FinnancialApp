import { LinearGradient } from 'expo-linear-gradient';
import { Link, useFocusEffect } from 'expo-router';
import { ChevronRight, WalletCards } from 'lucide-react-native';
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

export default function HomeScreen() {
  const { session, withAccessToken } = useAuth();
  const [accounts, setAccounts] = useState<FinancialAccount[] | null>(null);
  const [cashTotals, setCashTotals] = useState<AccountCashTotal[]>([]);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const entrance = useMemo(() => new Animated.Value(0), []);

  useFocusEffect(useCallback(() => {
    if (!session) return;
    let active = true;
    setAccounts(null);
    setCashTotals([]);
    setAccountsError(null);
    void withAccessToken((token) => Promise.all([listAccounts(token, { limit: 6 }), getAccountCashTotals(token)]))
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

  const translateY = entrance.interpolate({ inputRange: [0, 1], outputRange: [22, 0] });
  const opacity = entrance.interpolate({ inputRange: [0, 1], outputRange: [0.32, 1] });

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <LinearGradient colors={['#FFF9F3', '#F5FAF7', '#F3F3FF']} style={styles.flex}>
        <View pointerEvents="none" style={styles.backgroundMint} />
        <View pointerEvents="none" style={styles.backgroundPeach} />
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <Animated.View style={{ opacity, transform: [{ translateY }] }}>
            <View style={styles.topBar}>
              <BrandMark />
            </View>

            <Text style={styles.greeting}>Tus cuentas</Text>
            <Text style={styles.intro}>
              Saldos registrados, organizados por moneda.
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
                {accounts.slice(0, 5).map((account) => (
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
                {accounts.length > 5 ? (
                  <Link href="/accounts" asChild>
                    <Pressable accessibilityRole="button" style={styles.moreAccountsButton}>
                      <Text style={styles.moreAccountsText}>Ver todas las cuentas</Text>
                      <ChevronRight color={colors.forest} size={16} />
                    </Pressable>
                  </Link>
                ) : null}
              </View>
            ) : null}
          </Animated.View>
        </ScrollView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safeArea: { backgroundColor: '#FFF9F3', flex: 1 },
  backgroundMint: { backgroundColor: colors.mintBright, borderRadius: 100, height: 200, opacity: 0.2, position: 'absolute', right: -90, top: 70, width: 200 },
  backgroundPeach: { backgroundColor: colors.peach, borderRadius: 80, height: 160, left: -100, opacity: 0.22, position: 'absolute', top: 430, width: 160 },
  content: { paddingBottom: 34, paddingHorizontal: 20 },
  topBar: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', paddingTop: 12 },
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
  moreAccountsButton: { alignItems: 'center', flexDirection: 'row', gap: 6, justifyContent: 'center', minHeight: 46 },
  moreAccountsText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 12 },
  negativeBalance: { color: colors.coral },
  sectionTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 22, marginTop: 2 },
});
