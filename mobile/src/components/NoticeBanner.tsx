import { CircleAlert, CircleCheck, Info } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';

import { colors, fontFamily } from '@/theme';

type NoticeTone = 'error' | 'success' | 'info';

export function NoticeBanner({ message, tone = 'error' }: { message: string; tone?: NoticeTone }) {
  const Icon = tone === 'error' ? CircleAlert : tone === 'success' ? CircleCheck : Info;
  const color = tone === 'error' ? colors.coral : tone === 'success' ? colors.green : colors.lavenderDeep;

  return (
    <View
      accessibilityRole="alert"
      style={[styles.container, tone === 'error' && styles.error, tone === 'info' && styles.info]}
    >
      <Icon color={color} size={18} />
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-start',
    backgroundColor: colors.paleGreen,
    borderRadius: 16,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  error: { backgroundColor: colors.paleRed },
  info: { backgroundColor: '#F0EFFF' },
  message: {
    color: colors.ink,
    flex: 1,
    fontFamily: fontFamily.medium,
    fontSize: 13,
    lineHeight: 19,
  },
});
