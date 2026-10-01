import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { formatMoney } from '@/accounts/format';
import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';
import { createPlanningRecord, listPlanningRecords, type PlanningKind, type PlanningRecord } from './api';
import { displayFinancialDate, normalizePlanningDate, recordDate, validFinancialDate, validatePlanningInput } from './validation';

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
  const [recurrence, setRecurrence] = useState<'ONE_TIME' | 'MONTHLY'>('ONE_TIME');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
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
    const result = validatePlanningInput(kind, description, amount, currency, date, recurrence);
    if (result.error) { setFormError(result.error); return; }
    if (!result.input) return;
    submitting.current = true; setSaving(true); setFormError(null);
    try {
      await authenticated.current((token) => createPlanningRecord(token, kind, result.input));
      if (!mounted.current) return;
      setEditor(false); setDescription(''); setAmount('');
      const savedDate = 'expected_date' in result.input ? result.input.expected_date : result.input.due_date;
      setMessage(recurrence === 'MONTHLY'
        ? `Repetición mensual guardada desde ${displayFinancialDate(savedDate)}. Tus saldos no cambiaron.`
        : `Registro guardado para ${displayFinancialDate(savedDate)}. Tus saldos no cambiaron.`);
      reload(0);
    } catch (error) {
      if (mounted.current) setFormError(error instanceof ApiError ? error.message : 'No pudimos guardar el registro.');
    } finally {
      submitting.current = false;
      if (mounted.current) setSaving(false);
    }
  }

  const income = kind === 'income';
  return <View style={styles.card}>
    <Text accessibilityRole="header" style={styles.title}>{income ? 'Ingresos esperados' : 'Gastos y compromisos'}</Text>
    <Text style={styles.help}>{income ? 'Dinero que esperás cobrar. Registrarlo no aumenta el saldo de tus cuentas.' : 'Obligaciones que debés pagar. Registrarlas no ejecuta un pago ni cambia tus cuentas.'}</Text>
    {message && <Text accessibilityRole="alert" style={styles.help}>{message}</Text>}
    <Pressable accessibilityRole="button" disabled={saving} style={styles.button} onPress={() => { setEditor(!editor); setFormError(null); setMessage(null); }}>
      <Text style={styles.buttonText}>{editor ? 'Cerrar formulario' : income ? 'Agregar ingreso' : 'Agregar gasto o compromiso'}</Text>
    </Pressable>
    {editor && <View style={styles.form}>
      <Text style={styles.help}>Frecuencia</Text>
      <View style={styles.row}>{([{value: 'ONE_TIME', label: 'Una vez'}, {value: 'MONTHLY', label: 'Todos los meses'}] as const).map((option) => <Pressable key={option.value} accessibilityRole="button" accessibilityState={{selected: recurrence === option.value}} disabled={saving} onPress={() => setRecurrence(option.value)} style={[styles.button, styles.flex, recurrence === option.value && styles.selected]}><Text style={styles.buttonText}>{option.label}</Text></Pressable>)}</View>
      <FormField icon={null} label="Descripción" value={description} onChangeText={setDescription} editable={!saving} maxLength={100} placeholder={income ? 'Ej.: trabajo freelance' : 'Ej.: alquiler'} />
      <FormField icon={null} label="Importe (sin separadores de miles)" value={amount} onChangeText={setAmount} editable={!saving} keyboardType="decimal-pad" placeholder="Ej.: 15000,50" />
      <Text style={styles.help}>Moneda</Text>
      <View style={styles.row}>{(['ARS', 'USD'] as const).map((value) => <Pressable key={value} accessibilityRole="button" accessibilityState={{ selected: currency === value }} disabled={saving} onPress={() => setCurrency(value)} style={[styles.button, styles.flex, currency === value && styles.selected]}><Text style={styles.buttonText}>{value}</Text></Pressable>)}</View>
      <FormField icon={null} label={recurrence === 'MONTHLY' ? 'Primera fecha (DD/MM/AAAA)' : income ? 'Fecha esperada (DD/MM/AAAA)' : 'Vencimiento (DD/MM/AAAA)'} value={date} onChangeText={setDate} editable={!saving} autoCapitalize="none" maxLength={10} placeholder="15/10/2026" />
      {recurrence === 'MONTHLY' ? <View style={styles.preview}>
        <Text style={styles.name}>{validFinancialDate(normalizePlanningDate(date)) ? `Todos los meses, el día ${normalizePlanningDate(date).slice(8)}` : 'Elegí la primera fecha para fijar el día mensual'}</Text>
        <Text style={styles.help}>Si ese día no existe, usamos el último día del mes. Cada registro queda pendiente; no se cobra ni se paga automáticamente.</Text>
      </View> : <Text style={styles.help}>Por única vez · Pendiente. Podés registrar fechas anteriores.</Text>}
      {formError && <NoticeBanner message={formError} />}
      <PrimaryButton label={recurrence === 'MONTHLY' ? 'Guardar repetición mensual' : income ? 'Guardar ingreso' : 'Guardar compromiso'} loading={saving} onPress={() => { void save(); }} />
    </View>}
    {loading ? <ActivityIndicator accessibilityLabel="Cargando registros" color={colors.forest} /> : loadError ? <><NoticeBanner message={loadError} /><Pressable accessibilityRole="button" style={styles.button} onPress={() => reload()}><Text style={styles.buttonText}>Reintentar</Text></Pressable></> : records.length === 0 ? <Text style={styles.help}>No hay registros en esta página para el mes ni pendientes anteriores.</Text> : records.map((record) => <View key={record.id} style={styles.entry}>
      <Text style={styles.name}>{record.description}</Text>
      <Text style={styles.amount}>{formatMoney(record.amount, record.currency)}</Text>
      <Text style={styles.help}>{displayFinancialDate(recordDate(record))} · Pendiente · {record.recurrence === 'MONTHLY' ? 'Mensual' : 'Por única vez'}</Text>
      {recordDate(record) < today && <Text style={styles.overdue}>{income ? 'Fecha esperada vencida: todavía pendiente' : 'Vencido: todavía pendiente'}</Text>}
    </View>)}
    <Text style={styles.help}>Página {page + 1} · Fecha más antigua primero</Text>
    <View style={styles.row}>
      <Pressable accessibilityRole="button" disabled={loading || page === 0} style={[styles.button, styles.flex, (loading || page === 0) && styles.disabled]} onPress={() => reload(page - 1)}><Text style={styles.buttonText}>Anterior</Text></Pressable>
      <Pressable accessibilityRole="button" disabled={loading || !!loadError || !hasNext} style={[styles.button, styles.flex, (loading || !!loadError || !hasNext) && styles.disabled]} onPress={() => reload(page + 1)}><Text style={styles.buttonText}>Siguiente</Text></Pressable>
    </View>
    <Pressable accessibilityRole="button" disabled={loading} style={styles.button} onPress={() => reload(0)}><Text style={styles.buttonText}>Actualizar registros</Text></Pressable>
  </View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.white, borderColor: colors.line, borderWidth: 1, borderRadius: 20, gap: 12, padding: 17 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 21 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 19 },
  form: { gap: 12 }, row: { flexDirection: 'row', gap: 10 }, flex: { flex: 1 },
  preview: { backgroundColor: colors.paleGreen, borderRadius: 14, gap: 6, padding: 14 },
  entry: { borderBottomColor: colors.line, borderBottomWidth: 1, gap: 5, paddingVertical: 10 },
  name: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 16 },
  amount: { color: colors.forest, fontFamily: fontFamily.bold, fontSize: 19 },
  overdue: { color: colors.coral, fontFamily: fontFamily.semibold, fontSize: 12 },
  button: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 12, justifyContent: 'center', minHeight: 44, padding: 9 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
  selected: { borderWidth: 2, borderColor: colors.forest }, disabled: { opacity: 0.45 },
});
