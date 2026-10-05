import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { PlanningSheet } from '@/planning/PlanningSheet';
import { colors, fontFamily } from '@/theme';
import { exportUserData } from './api';
import { saveExport } from './saveExport';

export function DataControls({ disabled = false, onBusyChange }: { disabled?: boolean; onBusyChange: (busy: boolean) => void }) {
  const { withAccessToken, deleteAccount } = useAuth();
  const [action, setAction] = useState<'export' | 'delete' | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const submitting = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  async function run(next: 'export' | 'delete') {
    if (submitting.current) return;
    submitting.current = true; setAction(next); setError(null); onBusyChange(true);
    try {
      if (next === 'export') {
        const data = await withAccessToken(exportUserData);
        await saveExport(JSON.stringify(data, null, 2));
      } else {
        await deleteAccount(password);
      }
    } catch (failure) {
      if (mounted.current) setError(failure instanceof ApiError || failure instanceof Error ? failure.message : 'No pudimos completar la acción.');
    } finally { submitting.current = false; if (mounted.current) { setAction(null); onBusyChange(false); } }
  }

  return <View style={styles.group}>
    <Text style={styles.heading}>Tus datos financieros</Text>
    <Text style={styles.help}>Exportá tus cuentas, movimientos e historial en un archivo JSON. Contiene información privada: elegí dónde guardarlo.</Text>
    <PrimaryButton label="Exportar mis datos" loading={action === 'export'} disabled={disabled || action !== null} onPress={() => void run('export')} />
    {error && !deleting && <NoticeBanner message={error} />}
    <Pressable accessibilityRole="button" disabled={disabled || action !== null} style={styles.delete} onPress={() => { setDeleting(true); setPassword(''); setError(null); }}><Text style={styles.deleteText}>Eliminar mi cuenta y mis datos</Text></Pressable>
    {deleting && <PlanningSheet title="Eliminar mi cuenta" busy={action === 'delete'} onClose={() => { setDeleting(false); setPassword(''); setError(null); }}>
      <Text style={styles.help}>Se eliminarán permanentemente tu cuenta, saldos, movimientos, historial y sesiones de todos los dispositivos. Esta acción no se puede deshacer. Exportá tus datos antes si querés conservarlos.</Text>
      <FormField icon={null} label="Contraseña actual" value={password} onChangeText={setPassword} secureTextEntry editable={action !== 'delete'} autoCapitalize="none" />
      {error && <NoticeBanner message={error} />}
      <PrimaryButton label="Eliminar definitivamente" loading={action === 'delete'} disabled={!password || action !== null} onPress={() => void run('delete')} />
    </PlanningSheet>}
  </View>;
}

const styles = StyleSheet.create({
  group: { gap: 14, marginTop: 28 },
  heading: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 21 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
  delete: { minHeight: 44, justifyContent: 'center', alignItems: 'center' },
  deleteText: { color: colors.coral, fontFamily: fontFamily.semibold, fontSize: 12 },
});
