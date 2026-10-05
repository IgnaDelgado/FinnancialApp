import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { listAccounts, type FinancialAccount } from '@/accounts/api';
import { formatMoney } from '@/accounts/format';
import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';
import { confirmPlanningRecord, type PlanningKind, type PlanningRecord } from './api';

export function ConfirmationForm({ record, kind, onComplete, onCancel }: {
  record: PlanningRecord;
  kind: PlanningKind;
  onComplete: (record: PlanningRecord) => void;
  onCancel: () => void;
}) {
  const { withAccessToken, session } = useAuth();
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  const [alreadyIncluded, setAlreadyIncluded] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);
  const submitting = useRef(false);
  const mounted = useRef(true);
  const authenticated = useRef(withAccessToken);
  useEffect(() => { authenticated.current = withAccessToken; }, [withAccessToken]);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    let active = true;
    void authenticated.current((token) => listAccounts(token, { limit: 21, offset: page * 20 }))
      .then((result) => {
        if (!active) return;
        setAccounts(result.slice(0, 20)); setHasNext(result.length > 20); setLoading(false);
      }).catch((failure: unknown) => {
        if (!active) return;
        setLoadError(failure instanceof ApiError ? failure.message : 'No pudimos cargar las cuentas.');
        setLoading(false);
      });
    return () => { active = false; };
  }, [page, revision, session?.user.id]);

  function changePage(nextPage: number) {
    setLoading(true); setLoadError(null); setAccountId(null); setPage(nextPage);
  }

  function retryAccounts() {
    setLoading(true); setLoadError(null); setAccountId(null);
    setRevision((value) => value + 1);
  }

  async function confirm() {
    if (submitting.current || !accountId || alreadyIncluded === null) return;
    submitting.current = true; setSaving(true); setError(null);
    try {
      const result = await authenticated.current((token) =>
        confirmPlanningRecord(token, kind, record.id, accountId, alreadyIncluded));
      if (mounted.current) onComplete(result);
    } catch (failure) {
      if (mounted.current) setError(failure instanceof ApiError ? failure.message : 'No pudimos confirmar. Podés reintentar con la misma cuenta y opción.');
    } finally {
      submitting.current = false;
      if (mounted.current) setSaving(false);
    }
  }

  const matching = accounts.filter((account) => account.currency === record.currency);
  return <View style={styles.form}>
    <Text style={styles.title}>{kind === 'income' ? 'Confirmar cobro' : 'Confirmar pago'}</Text>
    <Text style={styles.help}>{record.description} · {formatMoney(record.amount, record.currency)}. Confirmás el importe completo.</Text>
    <Text style={styles.help}>Elegí la cuenta {record.currency} donde ocurrió.</Text>
    {loading ? <ActivityIndicator accessibilityLabel="Cargando cuentas" color={colors.forest} /> : loadError ? <>
      <NoticeBanner message={loadError} />
      <Pressable accessibilityRole="button" style={styles.option} onPress={retryAccounts}><Text style={styles.label}>Reintentar</Text></Pressable>
    </> : <>
      {matching.length === 0 && <Text style={styles.help}>No hay cuentas {record.currency} en esta página. Revisá otra página o agregá una cuenta en Mi dinero.</Text>}
      {matching.map((account) => <Pressable key={account.id} accessibilityRole="button" accessibilityState={{ selected: accountId === account.id }} disabled={saving} style={[styles.option, accountId === account.id && styles.selected]} onPress={() => setAccountId(account.id)}>
        <Text style={styles.label}>{account.name} · {formatMoney(account.current_balance, account.currency)}</Text>
      </Pressable>)}
      <View style={styles.row}>
        <Pressable accessibilityRole="button" disabled={saving || page === 0} style={[styles.option, styles.flex]} onPress={() => changePage(page - 1)}><Text style={styles.label}>Anterior</Text></Pressable>
        <Text style={styles.help}>Página {page + 1}</Text>
        <Pressable accessibilityRole="button" disabled={saving || !hasNext} style={[styles.option, styles.flex]} onPress={() => changePage(page + 1)}><Text style={styles.label}>Siguiente</Text></Pressable>
      </View>
    </>}
    <Text style={styles.help}>¿Este movimiento ya está incluido en el saldo que registraste?</Text>
    {([{ value: false, label: 'Actualizar saldo', help: kind === 'income' ? 'Sumar este cobro a la cuenta.' : 'Restar este pago de la cuenta.' },
      { value: true, label: 'Ya está incluido en el saldo', help: 'Confirmar sin volver a cambiar el saldo.' }] as const).map((option) =>
      <Pressable key={option.label} accessibilityRole="button" accessibilityState={{ selected: alreadyIncluded === option.value }} disabled={saving} style={[styles.option, alreadyIncluded === option.value && styles.selected]} onPress={() => setAlreadyIncluded(option.value)}>
        <Text style={styles.label}>{option.label}</Text><Text style={styles.help}>{option.help}</Text>
      </Pressable>)}
    <Text style={styles.help}>La confirmación quedará registrada. En esta versión no se puede deshacer desde la aplicación.</Text>
    {error && <NoticeBanner message={error} />}
    <PrimaryButton label={kind === 'income' ? 'Confirmar cobrado' : 'Confirmar pagado'} loading={saving} disabled={loading || !!loadError || !accountId || alreadyIncluded === null} onPress={() => { void confirm(); }} />
    <Pressable accessibilityRole="button" disabled={saving} style={styles.option} onPress={onCancel}><Text style={styles.label}>Cancelar</Text></Pressable>
  </View>;
}

const styles = StyleSheet.create({
  form: { backgroundColor: colors.canvas, borderRadius: 14, padding: 12, gap: 12 },
  title: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 17 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 19 },
  option: { backgroundColor: colors.paleGreen, borderRadius: 12, minHeight: 44, padding: 10, justifyContent: 'center', gap: 4 },
  label: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
  selected: { borderWidth: 2, borderColor: colors.forest },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 }, flex: { flex: 1 },
});
