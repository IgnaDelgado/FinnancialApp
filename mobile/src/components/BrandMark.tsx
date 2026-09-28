import { WalletCards } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';

import { colors, fontFamily } from '@/theme';

export function BrandMark({ inverted = false }: { inverted?: boolean }) {
  return (
    <View style={styles.row}>
      <View style={styles.icon}>
        <WalletCards color={colors.forestDeep} size={21} strokeWidth={2.2} />
      </View>
      <View>
        <Text style={[styles.name, inverted && styles.nameInverted]}>FINANCIAL PLAN</Text>
        <Text style={[styles.caption, inverted && styles.captionInverted]}>TU DINERO, CON INTENCIÓN</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { alignItems: 'center', flexDirection: 'row', gap: 11 },
  icon: {
    alignItems: 'center',
    backgroundColor: colors.mint,
    borderRadius: 13,
    height: 43,
    justifyContent: 'center',
    width: 43,
  },
  name: { color: colors.ink, fontFamily: fontFamily.bold, fontSize: 12, letterSpacing: 0.8 },
  nameInverted: { color: colors.white },
  caption: { color: colors.muted, fontFamily: fontFamily.medium, fontSize: 8, letterSpacing: 0.6, marginTop: 2 },
  captionInverted: { color: '#B9CBC4' },
});
