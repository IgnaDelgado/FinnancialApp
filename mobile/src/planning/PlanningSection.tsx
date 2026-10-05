import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import type { FinancialAccount } from '@/accounts/api';
import { formatMoney } from '@/accounts/format';
import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';
import { ConfirmationForm } from './ConfirmationForm';
import { AccountSelector } from './AccountSelector';
import { PlanningSheet } from './PlanningSheet';
import { createPlanningRecord, listPlanningRecords, type PlanningKind, type PlanningRecord } from './api';
import { displayFinancialDate, recordDate, validatePlanningInput } from './validation';

export function PlanningSection({ kind, today, period }: { kind: PlanningKind; today: string; period: string }) {
  const { withAccessToken, session, isBootstrapping } = useAuth();
  const ownerId = session?.user.id;
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [records, setRecords] = useState<PlanningRecord[]>([]);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editor, setEditor] = useState(false);
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState<'ARS' | 'USD'>('ARS');
  const [date, setDate] = useState(displayFinancialDate(period === today.slice(0, 7) ? today : `${period}-01`));
  const [recurrence, setRecurrence] = useState<'ONE_TIME' | 'MONTHLY'>('MONTHLY');
  const [account, setAccount] = useState<FinancialAccount | null>(null);
  const [history, setHistory] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null);
  const submitting = useRef(false);
  const mounted = useRef(true);
  const requestVersion = useRef(0);
  // Keep the latest auth operation without restarting reads on token rotation.
  const authenticated = useRef(withAccessToken);
  useEffect(() => { authenticated.current = withAccessToken; }, [withAccessToken]);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  useFocusEffect(useCallback(() => {
    // A revision explicitly refreshes the current page after writes or retries.
    void revision;
    const version = ++requestVersion.current;
    setLoading(true); setLoadError(null);
    if (isBootstrapping || !ownerId) return () => { requestVersion.current++; };
    const [year, month] = period.split('-');
    void authenticated.current((token) => listPlanningRecords(token, kind, year, month, page * 20))
      .then((result) => {
        if (version !== requestVersion.current) return;
        setRecords(result.slice(0, 20)); setHasNext(result.length > 20); setLoading(false);
      }).catch((error: unknown) => {
        if (version !== requestVersion.current) return;
        setLoadError(error instanceof ApiError ? error.message : 'No pudimos cargar los registros.'); setLoading(false);
      });
    return () => { requestVersion.current++; };
  }, [kind, page, revision, period, ownerId, isBootstrapping]));

  function reload(nextPage = page) {
    requestVersion.current++;
    setLoading(true); setLoadError(null); setPage(nextPage); setRevision((value) => value + 1);
  }

  async function save() {
    if (submitting.current) return;
    if (!account) { setFormError('Elegí la cuenta de este movimiento.'); return; }
    const result = validatePlanningInput(kind, description, amount, currency, date, recurrence);
    if (result.error) { setFormError(result.error); return; }
    if (!result.input) return;
    submitting.current = true; setSaving(true); setFormError(null);
    try {
      await authenticated.current((token) => createPlanningRecord(token, kind, { ...result.input, preferred_account_id: account.id }));
      if (!mounted.current) return;
      setEditor(false); setDescription(''); setAmount('');
      const savedDate = 'expected_date' in result.input ? result.input.expected_date : result.input.due_date;
      setMessage(`Guardado para ${displayFinancialDate(savedDate)} en ${account.name}.`);
      reload(0);
    } catch (error) {
      if (mounted.current) setFormError(error instanceof ApiError ? error.message : 'No pudimos guardar el registro.');
    } finally {
      submitting.current = false;
      if (mounted.current) setSaving(false);
    }
  }

  const income = kind === 'income';
  const pendingRecords = records.filter((record) => record.status === 'PLANNED');
  const completedRecords = records.filter((record) => record.status !== 'PLANNED');
  return <View style={styles.card}>
    <View style={styles.sectionHeading}>
      <Text accessibilityRole="header" style={styles.title}>{income ? 'Por cobrar' : 'Por pagar'}</Text>
      <Pressable accessibilityRole="button" disabled={saving} style={styles.add} onPress={() => { setEditor(true); setFormError(null); setMessage(null); }}>
        <Text style={styles.addText}>{income ? '+ Nuevo cobro' : '+ Nuevo pago'}</Text>
      </Pressable>
    </View>
    {message && <Text accessibilityRole="alert" style={styles.help}>{message}</Text>}
    {editor && <PlanningSheet title={income ? 'Nuevo cobro' : 'Nuevo pago'} onClose={() => setEditor(false)} busy={saving}>
      <View style={styles.row}>{(income ? ['Sueldo', 'Trabajo', 'Otro'] : ['Alquiler', 'Servicios', 'Tarjeta']).map((label) => <Pressable key={label} accessibilityRole="button" disabled={saving} style={[styles.button, styles.flex]} onPress={() => { setDescription(label); setRecurrence(label === 'Trabajo' || label === 'Otro' ? 'ONE_TIME' : 'MONTHLY'); }}><Text style={styles.buttonText}>{label}</Text></Pressable>)}</View>
      <Text style={styles.help}>¿Se repite?</Text>
      <View style={styles.row}>{([{value: 'ONE_TIME', label: 'Una vez'}, {value: 'MONTHLY', label: 'Todos los meses'}] as const).map((option) => <Pressable key={option.value} accessibilityRole="button" accessibilityState={{selected: recurrence === option.value}} disabled={saving} onPress={() => setRecurrence(option.value)} style={[styles.button, styles.flex, recurrence === option.value && styles.selected]}><Text style={styles.buttonText}>{option.label}</Text></Pressable>)}</View>
      <FormField icon={null} label="Descripción" value={description} onChangeText={setDescription} editable={!saving} maxLength={100} placeholder={income ? 'Ej.: trabajo freelance' : 'Ej.: alquiler'} />
      <AccountSelector value={account} disabled={saving} onChange={(selected) => { setAccount(selected); setCurrency(selected.currency); }} />
      <FormField icon={null} label={`Importe${account ? ` (${currency})` : ''}`} value={amount} onChangeText={setAmount} editable={!saving} keyboardType="decimal-pad" placeholder="Ej.: 15000,50" />
      <FormField icon={null} label={recurrence === 'MONTHLY' ? 'Primera fecha (DD/MM/AAAA)' : income ? 'Fecha esperada (DD/MM/AAAA)' : 'Vencimiento (DD/MM/AAAA)'} value={date} onChangeText={setDate} editable={!saving} autoCapitalize="none" maxLength={10} placeholder="15/10/2026" />
      <Text style={styles.help}>{recurrence === 'MONTHLY' ? 'La cuenta y el día quedan guardados para cada mes. ' : ''}Confirmá cuando ocurra para actualizar el saldo.</Text>
      {formError && <NoticeBanner message={formError} />}
      <PrimaryButton label={income ? 'Guardar cobro' : 'Guardar pago'} loading={saving} onPress={() => { void save(); }} />
    </PlanningSheet>}
    {loading ? <ActivityIndicator accessibilityLabel="Cargando registros" color={colors.forest} /> : loadError ? <><NoticeBanner message={loadError} /><Pressable accessibilityRole="button" style={styles.button} onPress={() => reload()}><Text style={styles.buttonText}>Reintentar</Text></Pressable></> : <>
    {pendingRecords.length === 0 && <View style={styles.empty}><Text style={styles.name}>{records.length ? 'Todo confirmado en esta página' : income ? 'Agregá tu sueldo o próximo cobro' : 'Agregá tu alquiler o gastos fijos'}</Text><Text style={styles.help}>{records.length ? 'Los movimientos confirmados están en el historial.' : 'Elegí una cuenta una vez y dejá preparado cada mes.'}</Text></View>}
    {pendingRecords.map((record) => <View key={record.id} style={styles.entry}>
      <View style={styles.entryHeader}><Text style={[styles.name, styles.flex]}>{record.description}</Text><Text style={styles.tag}>{record.recurrence === 'MONTHLY' ? 'Mensual' : 'Una vez'}</Text></View>
      <Text style={styles.amount}>{formatMoney(record.amount, record.currency)}</Text>
      <Text style={styles.help}>{record.preferred_account_name ?? 'Elegí la cuenta al confirmar'}</Text>
      <View style={styles.entryHeader}><Text style={recordDate(record) < today ? styles.overdue : styles.help}>{displayFinancialDate(recordDate(record))}{recordDate(record) < today ? ' · Pendiente' : recordDate(record) === today ? ' · Hoy' : ''}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel={`${income ? 'Cobré' : 'Pagué'} ${record.description}`} style={styles.confirmButton} onPress={() => { setConfirming(record.id); setMessage(null); }}><Text style={styles.confirmText}>{income ? 'Cobré' : 'Pagué'} →</Text></Pressable></View>
      {(confirming === record.id
        ? <ConfirmationForm key={`${ownerId}-${record.id}`} record={record} kind={kind} onCancel={() => setConfirming(null)} onComplete={(confirmed) => {
          setConfirming(null);
          setMessage(`${income ? 'Cobro' : 'Pago'} confirmado. ${confirmed.already_in_balance ? 'El saldo no cambió porque ya lo incluía.' : 'El saldo de la cuenta se actualizó.'}`);
          reload();
        }} />
        : null)}
    </View>)}
    {completedRecords.length > 0 && <>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: history }} style={styles.historyToggle} onPress={() => setHistory(!history)}><Text style={styles.help}>{history ? 'Ocultar' : 'Ver'} confirmados en esta página ({completedRecords.length}) {history ? '−' : '+'}</Text></Pressable>
      {history && completedRecords.map((record) => <View key={record.id} style={styles.historyEntry}><Text style={styles.name}>{record.description}</Text><Text style={styles.help}>{formatMoney(record.amount, record.currency)} · {income ? 'Cobrado' : 'Pagado'} · {displayFinancialDate(recordDate(record))}</Text></View>)}
    </>}
    </>}
    {(page > 0 || hasNext) && <><Text style={styles.help}>Página {page + 1}</Text><View style={styles.row}>
      <Pressable accessibilityRole="button" disabled={loading || page === 0} style={[styles.button, styles.flex, (loading || page === 0) && styles.disabled]} onPress={() => reload(page - 1)}><Text style={styles.buttonText}>Anterior</Text></Pressable>
      <Pressable accessibilityRole="button" disabled={loading || !!loadError || !hasNext} style={[styles.button, styles.flex, (loading || !!loadError || !hasNext) && styles.disabled]} onPress={() => reload(page + 1)}><Text style={styles.buttonText}>Siguiente</Text></Pressable>
    </View></>}
    <Pressable accessibilityRole="button" disabled={loading} style={styles.historyToggle} onPress={() => reload()}><Text style={styles.help}>↻ Actualizar</Text></Pressable>
  </View>;
}

const styles = StyleSheet.create({
  card: { gap: 14 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  add: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 8 }, addText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
  entryHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12 },
  tag: { color: colors.muted, fontFamily: fontFamily.medium, fontSize: 11 },
  confirmButton: { minHeight: 44, paddingHorizontal: 16, justifyContent: 'center', backgroundColor: colors.paleGreen, borderRadius: 12 },
  confirmText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
  empty: { backgroundColor: colors.white, borderRadius: 20, padding: 24, gap: 10 },
  historyToggle: { minHeight: 44, justifyContent: 'center', alignItems: 'center' },
  historyEntry: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: colors.line, gap: 5 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 21 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 19 },
  row: { flexDirection: 'row', gap: 10 }, flex: { flex: 1 },
  entry: { backgroundColor: colors.white, borderColor: colors.line, borderWidth: 1, borderRadius: 20, gap: 10, padding: 18 },
  name: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 16 },
  amount: { color: colors.forest, fontFamily: fontFamily.bold, fontSize: 19 },
  overdue: { color: colors.coral, fontFamily: fontFamily.semibold, fontSize: 12 },
  button: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 12, justifyContent: 'center', minHeight: 44, padding: 9 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
  selected: { borderWidth: 2, borderColor: colors.forest }, disabled: { opacity: 0.45 },
});
