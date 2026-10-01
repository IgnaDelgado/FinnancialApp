import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { NoticeBanner } from '@/components/NoticeBanner';
import { colors, fontFamily } from '@/theme';
import { listAccountBalanceHistory, type AccountBalanceSnapshot, type FinancialAccount } from './api';
import { formatMoney } from './format';

const PAGE_SIZE = 20;
const dateFormatter = new Intl.DateTimeFormat('es-AR', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Argentina/Cordoba',
});

export function BalanceHistory({ account }: { account: FinancialAccount }) {
  const { withAccessToken } = useAuth();
  const [page, setPage] = useState(0);
  const [attempt, setAttempt] = useState(0);
  const [entries, setEntries] = useState<AccountBalanceSnapshot[]>([]);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void withAccessToken((token) => listAccountBalanceHistory(token, account.id, {
      limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE,
    })).then((result) => {
      if (!active) return;
      setEntries(result.slice(0, PAGE_SIZE));
      setHasNextPage(result.length > PAGE_SIZE);
      setLoading(false);
    }).catch((caught: unknown) => {
      if (!active) return;
      setError(caught instanceof ApiError ? caught.message : 'No pudimos cargar el historial.');
      setLoading(false);
    });
    return () => { active = false; };
  }, [account.id, page, attempt, withAccessToken]);

  function changePage(nextPage: number) {
    setLoading(true);
    setError(null);
    setPage(nextPage);
  }

  function retry() {
    setLoading(true);
    setError(null);
    setAttempt((value) => value + 1);
  }

  return (
    <View style={styles.card}>
      <Text accessibilityRole="header" style={styles.title}>Historial de saldos</Text>
      <Text style={styles.help}>
        Saldos completos registrados, del más reciente al más antiguo. No son ingresos ni gastos. Horarios de Argentina.
      </Text>
      {loading ? <ActivityIndicator accessibilityLabel="Cargando historial" color={colors.forest} /> : error ? (
        <>
          <NoticeBanner message={error} />
          <Pressable accessibilityRole="button" onPress={retry} style={styles.button}>
            <Text style={styles.buttonText}>Reintentar historial</Text>
          </Pressable>
        </>
      ) : entries.length === 0 ? (
        <Text style={styles.help}>No hay saldos registrados en esta página.</Text>
      ) : entries.map((entry) => (
        <View key={entry.id} style={styles.entry}>
          <Text style={styles.help}>{dateFormatter.format(new Date(entry.recorded_at))}</Text>
          <Text style={[styles.amount, entry.balance.startsWith('-') && styles.negative]}>
            {formatMoney(entry.balance, account.currency)}
          </Text>
        </View>
      ))}
      <Text style={styles.help}>Página {page + 1}</Text>
      <View style={styles.pagination}>
        <Pressable accessibilityRole="button" disabled={loading || page === 0}
          onPress={() => changePage(page - 1)}
          style={[styles.button, (loading || page === 0) && styles.disabled]}>
          <Text style={styles.buttonText}>Más recientes</Text>
        </Pressable>
        <Pressable accessibilityRole="button" disabled={loading || !!error || !hasNextPage}
          onPress={() => changePage(page + 1)}
          style={[styles.button, (loading || !!error || !hasNextPage) && styles.disabled]}>
          <Text style={styles.buttonText}>Más antiguos</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.white, borderColor: colors.line, borderWidth: 1, borderRadius: 20, gap: 12, padding: 17 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 19 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18 },
  entry: { borderBottomColor: colors.line, borderBottomWidth: 1, gap: 4, paddingVertical: 8 },
  amount: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 16 },
  negative: { color: colors.coral },
  pagination: { flexDirection: 'row', gap: 10 },
  button: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 12, flex: 1, justifyContent: 'center', minHeight: 44, padding: 8 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 12 },
  disabled: { opacity: 0.45 },
});
