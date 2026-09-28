import { LinearGradient } from 'expo-linear-gradient';
import { ArrowRight } from 'lucide-react-native';
import { useMemo } from 'react';
import { ActivityIndicator, Animated, Pressable, StyleSheet, Text } from 'react-native';

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
  const scale = useMemo(() => new Animated.Value(1), []);
  const unavailable = disabled || loading;
  const contentColor = unavailable ? colors.green : colors.white;

  function animate(toValue: number) {
    Animated.spring(scale, {
      damping: 16,
      mass: 0.6,
      stiffness: 260,
      toValue,
      useNativeDriver: true,
    }).start();
  }

  return (
    <Animated.View style={[styles.shadow, { transform: [{ scale }] }, unavailable && styles.disabled]}>
      <Pressable
        accessibilityRole="button"
        disabled={unavailable}
        onPress={onPress}
        onPressIn={() => animate(0.975)}
        onPressOut={() => animate(1)}
      >
        <LinearGradient
          colors={unavailable ? ['#E5EFEA', '#D8E7E0'] : [colors.forest, '#4A9180']}
          end={{ x: 1, y: 0.8 }}
          start={{ x: 0, y: 0 }}
          style={styles.button}
        >
          <Text style={[styles.label, { color: contentColor }]}>{label}</Text>
          {loading ? (
            <ActivityIndicator color={contentColor} />
          ) : (
            <ArrowRight color={contentColor} size={20} strokeWidth={2.2} />
          )}
        </LinearGradient>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  shadow: {
    borderRadius: 18,
    shadowColor: colors.shadow,
    shadowOffset: { height: 8, width: 0 },
    shadowOpacity: 0.18,
    shadowRadius: 15,
  },
  button: {
    alignItems: 'center',
    borderRadius: 18,
    flexDirection: 'row',
    justifyContent: 'space-between',
    minHeight: 58,
    paddingHorizontal: 20,
  },
  disabled: { shadowOpacity: 0 },
  label: { fontFamily: fontFamily.bold, fontSize: 15 },
});
