import { Eye, EyeOff } from 'lucide-react-native';
import { useState, type ComponentProps, type ReactNode } from 'react';
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
  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.block}>
      <Text style={styles.label}>{label}</Text>
      <View style={[styles.inputShell, focused && styles.inputFocused]}>
        {icon}
        <TextInput
          {...inputProps}
          onBlur={(event) => {
            setFocused(false);
            inputProps.onBlur?.(event);
          }}
          onFocus={(event) => {
            setFocused(true);
            inputProps.onFocus?.(event);
          }}
          placeholderTextColor="#A2AAA7"
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
  block: { gap: 7 },
  label: { color: colors.slate, fontFamily: fontFamily.semibold, fontSize: 12.5, marginLeft: 2 },
  inputShell: {
    alignItems: 'center',
    backgroundColor: colors.field,
    borderColor: colors.line,
    borderRadius: 17,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 11,
    minHeight: 58,
    paddingHorizontal: 16,
  },
  inputFocused: {
    backgroundColor: colors.white,
    borderColor: colors.mint,
    borderWidth: 1.5,
    shadowColor: colors.mint,
    shadowOffset: { height: 4, width: 0 },
    shadowOpacity: 0.18,
    shadowRadius: 12,
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
