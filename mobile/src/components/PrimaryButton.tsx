import { ArrowRight } from 'lucide-react-native';
import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { colors, fontFamily } from '@/theme';

export function PrimaryButton({
  disabled = false,
  label,
  loading = false,
  onPress,
}: {
  disabled?: boolean;
  label: string;
  loading?: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        pressed && styles.pressed,
        (disabled || loading) && styles.disabled,
      ]}
    >
      <Text style={styles.label}>{label}</Text>
      {loading ? (
        <ActivityIndicator color={colors.forestDeep} />
      ) : (
        <ArrowRight color={colors.forestDeep} size={20} strokeWidth={2.2} />
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    backgroundColor: colors.mint,
    borderRadius: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    minHeight: 56,
    paddingHorizontal: 18,
  },
  pressed: { opacity: 0.82, transform: [{ scale: 0.995 }] },
  disabled: { opacity: 0.55 },
  label: { color: colors.forestDeep, fontFamily: fontFamily.bold, fontSize: 15 },
});
