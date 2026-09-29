import { Image, StyleSheet, Text, View } from 'react-native';

import { colors, fontFamily } from '@/theme';

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <View style={styles.row}>
      <Image
        accessibilityIgnoresInvertColors
        source={require('../../assets/financial-plan-icon.png')}
        style={[styles.icon, compact && styles.iconCompact]}
      />
      {!compact ? (
        <View>
          <Text style={styles.name}>Financial Plan</Text>
          <Text style={styles.caption}>TU DINERO, CON INTENCIÓN</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { alignItems: 'center', flexDirection: 'row', gap: 12 },
  icon: {
    borderRadius: 14,
    height: 46,
    width: 46,
  },
  iconCompact: { borderRadius: 13, height: 42, width: 42 },
  name: { color: colors.ink, fontFamily: fontFamily.displayBold, fontSize: 15, letterSpacing: -0.25 },
  caption: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 7.5, letterSpacing: 0.85, marginTop: 2 },
});
