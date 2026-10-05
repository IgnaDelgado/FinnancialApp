import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { listAccounts, type Currency, type FinancialAccount } from '@/accounts/api';
import { formatMoney } from '@/accounts/format';
import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { NoticeBanner } from '@/components/NoticeBanner';
import { colors, fontFamily } from '@/theme';

export function AccountSelector({ value, onChange, currency, disabled = false }: {
  value: FinancialAccount | null; onChange: (account: FinancialAccount) => void;
  currency?: Currency; disabled?: boolean;
}) {
  const { withAccessToken, session } = useAuth();
  const authenticated = useRef(withAccessToken);
  useEffect(() => { authenticated.current = withAccessToken; }, [withAccessToken]);
  const [expanded, setExpanded] = useState(!value);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState(false);
  useEffect(() => {
    if (!expanded) return;
    let active = true;
    void authenticated.current((token) => listAccounts(token, { limit: 21, offset: page * 20 }))
      .then((result) => {
        if (!active) return;
        setAccounts(result.slice(0, 20)); setHasNext(result.length > 20); setLoading(false);
      }).catch((failure: unknown) => {
        if (!active) return;
        setError(failure instanceof ApiError ? failure.message : 'No pudimos cargar las cuentas.'); setLoading(false);
      });
    return () => { active = false; };
  }, [expanded, page, revision, session?.user.id]);
  function reload(nextPage = page) {
    setLoading(true); setError(null); setPage(nextPage); setRevision((count) => count + 1);
  }
  const matching = accounts.filter((account) => !currency || account.currency === currency);
  return <View style={styles.group}>
    <Text style={styles.label}>Cuenta</Text>
    {value && <Pressable accessibilityRole="button" accessibilityLabel={`Cambiar cuenta ${value.name}`} disabled={disabled} style={styles.selected} onPress={() => { if (!expanded) reload(); setExpanded(!expanded); }}>
      <View style={styles.flex}><Text style={styles.name}>{value.name}</Text><Text style={styles.help}>{value.currency} · Saldo {formatMoney(value.current_balance, value.currency)}</Text></View>
      <Text style={styles.change}>{expanded ? 'Cerrar' : 'Cambiar'}</Text>
    </Pressable>}
    {expanded && <View style={styles.list}>
      {loading ? <ActivityIndicator accessibilityLabel="Cargando cuentas" color={colors.forest} /> : error ? <>
        <NoticeBanner message={error} /><Pressable accessibilityRole="button" disabled={disabled} onPress={() => reload()}><Text style={styles.change}>Reintentar</Text></Pressable>
      </> : <>
        {matching.length === 0 && <Text style={styles.help}>No hay cuentas {currency ?? ''} en esta página. Podés agregar una en Mi dinero.</Text>}
        {matching.map((account) => <Pressable key={account.id} accessibilityRole="button" disabled={disabled} style={styles.option} onPress={() => { onChange(account); setExpanded(false); }}><Text style={styles.name}>{account.name}</Text><Text style={styles.help}>{formatMoney(account.current_balance, account.currency)}</Text></Pressable>)}
        {(page > 0 || hasNext) && <View style={styles.navigation}>
          <Pressable accessibilityRole="button" disabled={disabled || page === 0} onPress={() => reload(page - 1)}><Text style={styles.change}>Anterior</Text></Pressable>
          <Text style={styles.help}>Página {page + 1}</Text>
          <Pressable accessibilityRole="button" disabled={disabled || !hasNext} onPress={() => reload(page + 1)}><Text style={styles.change}>Siguiente</Text></Pressable>
        </View>}
      </>}
    </View>}
  </View>;
}

const styles = StyleSheet.create({
  group: { gap: 8 }, label: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  selected: { backgroundColor: colors.field, borderRadius: 14, flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
  flex: { flex: 1 }, name: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 14 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18 },
  change: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13, paddingVertical: 10 },
  list: { borderColor: colors.line, borderWidth: 1, borderRadius: 14, padding: 12, gap: 6 },
  option: { paddingVertical: 10, borderBottomColor: colors.line, borderBottomWidth: 1, gap: 4 },
  navigation: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
});
