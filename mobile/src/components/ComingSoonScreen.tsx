import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, fontFamily } from '@/theme';

export function ComingSoonScreen({ title, description, icon }: { title: string; description: string; icon: ReactNode }) {
  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <View style={styles.content}>
        <View style={styles.icon}>{icon}</View>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
        <View style={styles.notice}>
          <Text style={styles.noticeTitle}>Próximamente</Text>
          <Text style={styles.noticeText}>Esta sección todavía no registra ni calcula información. Tus cuentas siguen disponibles en la pestaña Cuentas.</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  content: { flex: 1, paddingHorizontal: 20, paddingTop: 28 },
  icon: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 20, height: 58, justifyContent: 'center', width: 58 },
  title: { color: colors.ink, fontFamily: fontFamily.displayBold, fontSize: 32, marginTop: 20 },
  description: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 14, lineHeight: 21, marginTop: 5 },
  notice: { backgroundColor: colors.white, borderColor: colors.line, borderRadius: 20, borderWidth: 1, marginTop: 30, padding: 20 },
  noticeTitle: { color: colors.forest, fontFamily: fontFamily.displayMedium, fontSize: 19 },
  noticeText: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20, marginTop: 8 },
});
