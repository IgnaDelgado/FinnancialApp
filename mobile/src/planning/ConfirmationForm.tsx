import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { getAccount, type FinancialAccount } from '@/accounts/api';
import { formatMoney } from '@/accounts/format';
import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';
import { AccountSelector } from './AccountSelector';
import { PlanningSheet } from './PlanningSheet';
import { confirmPlanningRecord, type PlanningKind, type PlanningRecord } from './api';

export function ConfirmationForm({ record, kind, onComplete, onCancel }: {
  record: PlanningRecord; kind: PlanningKind;
  onComplete: (record: PlanningRecord) => void; onCancel: () => void;
}) {
  const { withAccessToken } = useAuth();
  const authenticated = useRef(withAccessToken);
  useEffect(() => { authenticated.current = withAccessToken; }, [withAccessToken]);
  const [account, setAccount] = useState<FinancialAccount | null>(null);
  const [loading, setLoading] = useState(!!record.preferred_account_id);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [remember, setRemember] = useState(record.recurrence === 'MONTHLY' && !record.preferred_account_id);
  const submitting = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    let active = true;
    const id = record.preferred_account_id;
    if (id) void authenticated.current((token) => getAccount(token, id)).then((result) => {
      if (!active) return;
      if (result.currency === record.currency) setAccount(result);
      setLoading(false);
    }).catch(() => {
      if (active) { setLoading(false); setError('La cuenta guardada ya no está disponible. Elegí otra.'); }
    });
    return () => { active = false; };
  }, [record.preferred_account_id, record.currency]);

  async function confirm(included: boolean) {
    if (submitting.current || !account) return;
    submitting.current = true; setSaving(true); setError(null);
    try {
      const result = await authenticated.current((token) => confirmPlanningRecord(token, kind, record.id, account.id, included, remember));
      if (mounted.current) onComplete(result);
    } catch (failure) {
      if (mounted.current) setError(failure instanceof ApiError ? failure.message : 'No pudimos confirmar. Podés reintentar.');
    } finally { submitting.current = false; if (mounted.current) setSaving(false); }
  }

  const income = kind === 'income';
  return <PlanningSheet title={income ? 'Confirmar cobro' : 'Confirmar pago'} onClose={onCancel} busy={saving}>
    <View style={styles.summary}><Text style={styles.name}>{record.description}</Text><Text style={styles.amount}>{formatMoney(record.amount, record.currency)}</Text></View>
    {loading ? <ActivityIndicator color={colors.forest} accessibilityLabel="Cargando cuenta" /> : <AccountSelector value={account} currency={record.currency} disabled={saving} onChange={(next) => { setAccount(next); setError(null); }} />}
    {record.recurrence === 'MONTHLY' && account?.id !== record.preferred_account_id && <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: remember }} disabled={saving} style={styles.remember} onPress={() => setRemember(!remember)}><Text style={styles.help}>{remember ? '☑' : '☐'} Usar esta cuenta todos los meses</Text></Pressable>}
    <Text style={styles.help}>{income ? 'Se sumará este importe a la cuenta.' : 'Se restará este importe de la cuenta.'} Podés corregir una confirmación desde el historial de Movimientos.</Text>
    {error && <NoticeBanner message={error} />}
    <PrimaryButton label={income ? 'Cobré · actualizar saldo' : 'Pagué · actualizar saldo'} loading={saving} disabled={loading || !account} onPress={() => { void confirm(false); }} />
    <Pressable accessibilityRole="button" disabled={saving || loading || !account} style={styles.secondary} onPress={() => { void confirm(true); }}><Text style={styles.secondaryText}>Ya estaba incluido en el saldo</Text></Pressable>
  </PlanningSheet>;
}

const styles = StyleSheet.create({
  summary: { gap: 5, paddingBottom: 8 }, name: { color: colors.muted, fontFamily: fontFamily.medium, fontSize: 15 },
  amount: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 30 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18 },
  remember: { minHeight: 44, justifyContent: 'center' },
  secondary: { minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  secondaryText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
});
