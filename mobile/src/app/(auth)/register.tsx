import { Check, KeyRound, Mail, ShieldCheck } from 'lucide-react-native';
import { Link } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import type { Currency } from '@/auth/types';
import { AuthShell } from '@/components/AuthShell';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [currency, setCurrency] = useState<Currency>('ARS');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = email.trim().length > 0 && password.length >= 8 && confirmation.length > 0;

  async function handleSubmit() {
    if (!canSubmit || submitting) return;
    if (password !== confirmation) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await signUp({ email: email.trim(), password, reference_currency: currency });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'No pudimos crear la cuenta.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Crear cuenta"
    >
      <View style={styles.fields}>
        <FormField
          autoCapitalize="none"
          autoComplete="email"
          autoCorrect={false}
          icon={<Mail color={colors.muted} size={19} />}
          keyboardType="email-address"
          label="Correo electrónico"
          onChangeText={setEmail}
          placeholder="nombre@correo.com"
          value={email}
        />
        <FormField
          autoCapitalize="none"
          autoComplete="new-password"
          icon={<KeyRound color={colors.muted} size={19} />}
          label="Contraseña · mínimo 8 caracteres"
          onChangeText={setPassword}
          onToggleSecret={() => setShowPassword((current) => !current)}
          placeholder="Creá una frase segura"
          secure
          showSecret={showPassword}
          value={password}
        />
        <FormField
          autoCapitalize="none"
          autoComplete="new-password"
          icon={<ShieldCheck color={colors.muted} size={19} />}
          label="Confirmar contraseña"
          onChangeText={setConfirmation}
          onSubmitEditing={handleSubmit}
          placeholder="Repetí tu contraseña"
          returnKeyType="done"
          secure
          showSecret={showPassword}
          value={confirmation}
        />
      </View>

      <Text style={styles.currencyLabel}>Moneda de referencia</Text>
      <View accessibilityRole="radiogroup" style={styles.currencyRow}>
        {(['ARS', 'USD'] as const).map((option) => {
          const selected = currency === option;
          return (
            <Pressable
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              key={option}
              onPress={() => setCurrency(option)}
              style={[styles.currencyOption, selected && styles.currencySelected]}
            >
              <View>
                <Text style={[styles.currencyCode, selected && styles.currencyCodeSelected]}>{option}</Text>
                <Text style={styles.currencyName}>{option === 'ARS' ? 'Peso argentino' : 'Dólar estadounidense'}</Text>
              </View>
              {selected ? <Check color={colors.forest} size={18} /> : null}
            </Pressable>
          );
        })}
      </View>

      {error ? <NoticeBanner message={error} /> : null}
      <PrimaryButton
        disabled={!canSubmit}
        label="Crear mi cuenta"
        loading={submitting}
        onPress={() => void handleSubmit()}
      />

      <View style={styles.switchRow}>
        <Text style={styles.switchCopy}>¿Ya tenés cuenta?</Text>
        <Link href="/(auth)/login" asChild>
          <Pressable><Text style={styles.switchLink}>Iniciar sesión</Text></Pressable>
        </Link>
      </View>
    </AuthShell>
  );
}

const styles = StyleSheet.create({
  fields: { gap: 7 },
  currencyLabel: { color: colors.slate, fontFamily: fontFamily.semibold, fontSize: 12.5, marginTop: 2 },
  currencyRow: { flexDirection: 'row', gap: 9, marginBottom: 3, marginTop: 3 },
  currencyOption: {
    alignItems: 'center',
    backgroundColor: colors.field,
    borderColor: colors.line,
    borderRadius: 14,
    borderWidth: 1,
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    minHeight: 50,
    paddingHorizontal: 12,
  },
  currencySelected: { backgroundColor: colors.softMint, borderColor: colors.mint },
  currencyCode: { color: colors.muted, fontFamily: fontFamily.bold, fontSize: 14 },
  currencyCodeSelected: { color: colors.forest },
  currencyName: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 10, marginTop: 2 },
  switchRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 5, justifyContent: 'center', marginTop: 2 },
  switchCopy: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13 },
  switchLink: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 13 },
});
