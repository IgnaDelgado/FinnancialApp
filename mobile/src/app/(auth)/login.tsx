import { KeyRound, Mail, RotateCcw, ShieldCheck } from 'lucide-react-native';
import { Link } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import { AuthShell } from '@/components/AuthShell';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PrimaryButton } from '@/components/PrimaryButton';
import { colors, fontFamily } from '@/theme';

export default function LoginScreen() {
  const { restoreError, retryRestore, signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = email.trim().length > 0 && password.length > 0;

  async function handleSubmit() {
    if (!canSubmit || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await signIn({ email: email.trim(), password });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'No pudimos iniciar sesión.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      eyebrow="TU PLAN EMPIEZA ACÁ"
      subtitle="Volvé a ver cuánto podés usar hoy y cómo avanzan tus objetivos."
      title={'Tu dinero,\ncon un plan.'}
    >
      <View style={styles.heading}>
        <Text style={styles.formTitle}>Bienvenido de nuevo</Text>
        <Text style={styles.formSubtitle}>Ingresá con el correo de tu cuenta.</Text>
      </View>

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
          returnKeyType="next"
          value={email}
        />
        <FormField
          autoCapitalize="none"
          autoComplete="current-password"
          icon={<KeyRound color={colors.muted} size={19} />}
          label="Contraseña"
          onChangeText={setPassword}
          onSubmitEditing={handleSubmit}
          onToggleSecret={() => setShowPassword((current) => !current)}
          placeholder="Tu contraseña"
          returnKeyType="done"
          secure
          showSecret={showPassword}
          value={password}
        />
      </View>

      {error ? <NoticeBanner message={error} /> : null}
      {restoreError && !error ? (
        <View style={styles.restoreBox}>
          <NoticeBanner message={restoreError} tone="info" />
          <Pressable onPress={() => void retryRestore()} style={styles.retryButton}>
            <RotateCcw color={colors.green} size={16} />
            <Text style={styles.retryText}>Reintentar sesión</Text>
          </Pressable>
        </View>
      ) : null}

      <PrimaryButton
        disabled={!canSubmit}
        label="Entrar a mi espacio"
        loading={submitting}
        onPress={() => void handleSubmit()}
      />

      <View style={styles.switchRow}>
        <Text style={styles.switchCopy}>¿Todavía no tenés una cuenta?</Text>
        <Link href="/(auth)/register" asChild>
          <Pressable><Text style={styles.switchLink}>Crear cuenta</Text></Pressable>
        </Link>
      </View>

      <View style={styles.securityNote}>
        <ShieldCheck color={colors.green} size={18} />
        <Text style={styles.securityCopy}>
          Tu contraseña viaja al servidor para validarse y nunca se guarda en el dispositivo.
        </Text>
      </View>
    </AuthShell>
  );
}

const styles = StyleSheet.create({
  heading: { gap: 4 },
  formTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 25 },
  formSubtitle: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 14, lineHeight: 20 },
  fields: { gap: 16, marginBottom: 18, marginTop: 23 },
  restoreBox: { gap: 7 },
  retryButton: { alignItems: 'center', alignSelf: 'flex-start', flexDirection: 'row', gap: 7, paddingVertical: 4 },
  retryText: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 12 },
  switchRow: { alignItems: 'center', flexDirection: 'row', gap: 5, justifyContent: 'center', marginTop: 20 },
  switchCopy: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13 },
  switchLink: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 13 },
  securityNote: {
    alignItems: 'flex-start',
    borderTopColor: colors.line,
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: 9,
    marginTop: 24,
    paddingTop: 18,
  },
  securityCopy: { color: colors.muted, flex: 1, fontFamily: fontFamily.body, fontSize: 11, lineHeight: 17 },
});
