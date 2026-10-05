import { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { ApiError } from '@/auth/api';
import { formatMoney } from '@/accounts/format';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';
import { correctPlanningRecord, editMonthlyPlan, stopMonthlyPlan, type PlanningKind, type PlanningRecord } from './api';
import { displayFinancialDate, monthAtOffset, validatePlanningInput } from './validation';
import { PlanningSheet } from './PlanningSheet';

export type MaintenanceAction = 'edit' | 'stop' | 'correct';

export function MaintenanceForm({ action, record, kind, today, period, onClose, onComplete }: {
  action: MaintenanceAction; record: PlanningRecord; kind: PlanningKind; today: string; period: string;
  onClose: () => void; onComplete: (message: string) => void;
}) {
  const { withAccessToken } = useAuth();
  const [amount, setAmount] = useState(record.amount);
  const [date, setDate] = useState(displayFinancialDate(`${action === 'edit' ? monthAtOffset(today, 1) : period}-01`));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submitting = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const title = action === 'edit' ? 'Cambiar repetición' : action === 'stop' ? 'Detener repetición' : 'Corregir confirmación';

  async function save() {
    if (submitting.current) return;
    let iso = '';
    if (action !== 'correct') {
      const validated = validatePlanningInput('income', record.description, amount, record.currency, date, 'MONTHLY');
      if (validated.error || !validated.input || !('expected_date' in validated.input)) { setError(validated.error ?? 'Revisá la fecha.'); return; }
      iso = validated.input.expected_date;
      if (action === 'edit' && iso.slice(0, 7) <= today.slice(0, 7)) { setError('Elegí un mes futuro.'); return; }
      if (!record.template_id) return;
    }
    submitting.current = true; setSaving(true); setError(null);
    try {
      if (action === 'correct') {
        const correction = await withAccessToken((token) => correctPlanningRecord(token, kind, record));
        if (!mounted.current) return;
        onComplete(correction.already_in_balance ? 'Confirmación corregida. El saldo no cambió.' : 'Confirmación corregida. Se aplicó el ajuste inverso al saldo actual.');
      } else if (action === 'stop') {
        await withAccessToken((token) => stopMonthlyPlan(token, record.template_id!, `${iso.slice(0, 7)}-01`));
        if (!mounted.current) return;
        onComplete(`Repetición detenida desde ${iso.slice(0, 7)}. Los movimientos confirmados se conservaron.`);
      } else {
        await withAccessToken((token) => editMonthlyPlan(token, record.template_id!, amount.trim().replace(',', '.'), iso));
        if (!mounted.current) return;
        onComplete('Repetición actualizada para los meses futuros. Los movimientos confirmados se conservaron.');
      }
    } catch (failure) {
      if (mounted.current) setError(failure instanceof ApiError ? failure.message : 'No pudimos guardar. Actualizá la lista antes de reintentar.');
    } finally { submitting.current = false; if (mounted.current) setSaving(false); }
  }

  return <PlanningSheet title={title} busy={saving} onClose={onClose}>
    <Text style={styles.name}>{record.description} · {formatMoney(record.amount, record.currency)}</Text>
    {action === 'correct' ? <Text style={styles.help}>{record.already_in_balance ? 'Se quitará esta confirmación sin cambiar el saldo, porque ya estaba incluido.' : `Se ${kind === 'income' ? 'restará' : 'sumará'} ${formatMoney(record.amount, record.currency)} al saldo actual de la cuenta original. No se restaurará un saldo anterior.`} El historial se conserva. Después podés confirmar de nuevo. Si la repetición ya fue detenida para ese mes, el movimiento quedará cancelado.</Text> : <>
      {action === 'edit' && <FormField icon={null} label={`Nuevo importe (${record.currency})`} value={amount} onChangeText={setAmount} editable={!saving} keyboardType="decimal-pad" />}
      <FormField icon={null} label={action === 'edit' ? 'Primera fecha del cambio (DD/MM/AAAA)' : 'Fecha del mes desde el que se detiene (DD/MM/AAAA)'} value={date} onChangeText={setDate} editable={!saving} maxLength={10} />
      <Text style={styles.help}>{action === 'edit' ? 'El importe y el día cambian desde ese mes futuro. Los meses anteriores y movimientos confirmados se conservan.' : 'Se cancelan sólo los movimientos pendientes desde ese mes inclusive. No cambia el saldo y se conservan los confirmados. Para reiniciar, creá una nueva repetición.'}</Text>
    </>}
    {error && <NoticeBanner message={error} />}
    <PrimaryButton label={action === 'correct' ? 'Confirmar corrección' : action === 'stop' ? 'Detener desde ese mes' : 'Guardar cambio futuro'} loading={saving} onPress={() => void save()} />
  </PlanningSheet>;
}

const styles = StyleSheet.create({
  name: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 16 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
});
