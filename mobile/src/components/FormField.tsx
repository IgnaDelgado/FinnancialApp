import { Eye, EyeOff } from 'lucide-react-native';
import type { ComponentProps, ReactNode } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { colors, fontFamily } from '@/theme';

type TextInputProps = ComponentProps<typeof TextInput>;

export function FormField({
  icon,
  label,
  secure,
  showSecret,
  onToggleSecret,
  ...inputProps
}: TextInputProps & {
  icon: ReactNode;
  label: string;
  secure?: boolean;
  showSecret?: boolean;
  onToggleSecret?: () => void;
}) {
  return (
    <View style={styles.block}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputShell}>
        {icon}
        <TextInput
          {...inputProps}
          placeholderTextColor="#99A29C"
          secureTextEntry={secure && !showSecret}
          style={styles.input}
        />
        {secure && onToggleSecret ? (
          <Pressable
            accessibilityLabel={showSecret ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            hitSlop={10}
            onPress={onToggleSecret}
          >
            {showSecret ? <EyeOff color={colors.muted} size={19} /> : <Eye color={colors.muted} size={19} />}
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: 8 },
  label: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  inputShell: {
    alignItems: 'center',
    backgroundColor: colors.field,
    borderColor: colors.line,
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 11,
    minHeight: 56,
    paddingHorizontal: 15,
  },
  input: {
    color: colors.ink,
    flex: 1,
    fontFamily: fontFamily.body,
    fontSize: 15,
    minHeight: 52,
    paddingVertical: 8,
  },
});
