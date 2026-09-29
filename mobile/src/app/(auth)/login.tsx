import { KeyRound, Mail, RotateCcw } from 'lucide-react-native';
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
      title="Iniciar sesión"
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
        label="Continuar"
        loading={submitting}
        onPress={() => void handleSubmit()}
      />

      <View style={styles.switchRow}>
        <Text style={styles.switchCopy}>¿No tenés cuenta?</Text>
        <Link href="/(auth)/register" asChild>
          <Pressable><Text style={styles.switchLink}>Crear cuenta</Text></Pressable>
        </Link>
      </View>
    </AuthShell>
  );
}

const styles = StyleSheet.create({
  fields: { gap: 12 },
  restoreBox: { gap: 5 },
  retryButton: { alignItems: 'center', alignSelf: 'flex-start', flexDirection: 'row', gap: 7, paddingVertical: 4 },
  retryText: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 12 },
  switchRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 5, justifyContent: 'center', marginTop: 8 },
  switchCopy: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13 },
  switchLink: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 13 },
});
