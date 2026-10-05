import type { ReactNode } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, fontFamily } from '@/theme';

export function PlanningSheet({ title, children, onClose, busy = false }: {
  title: string; children: ReactNode; onClose: () => void; busy?: boolean;
}) {
  return <Modal transparent animationType="fade" visible onRequestClose={() => { if (!busy) onClose(); }}>
    <SafeAreaView style={styles.overlay}>
      <View style={styles.panel}>
        <View style={styles.header}>
          <Text accessibilityRole="header" style={styles.title}>{title}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Cerrar" disabled={busy} style={styles.close} onPress={onClose}><Text style={styles.closeText}>×</Text></Pressable>
        </View>
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>{children}</ScrollView>
      </View>
    </SafeAreaView>
  </Modal>;
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(18,62,55,0.35)', justifyContent: 'center', padding: 16 },
  panel: { backgroundColor: colors.white, borderRadius: 24, maxHeight: '92%', width: '100%', maxWidth: 520, alignSelf: 'center', overflow: 'hidden' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  title: { flex: 1, color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 23 },
  close: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  closeText: { color: colors.muted, fontSize: 28 },
  content: { padding: 20, paddingTop: 8, gap: 16 },
});
