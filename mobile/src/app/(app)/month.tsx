import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { PlanningKind } from '@/planning/api';
import { PlanningSection } from '@/planning/PlanningSection';
import { financialDate, monthAtOffset } from '@/planning/validation';
import { colors, fontFamily } from '@/theme';

export default function MonthScreen() {
  const [today, setToday] = useState(financialDate);
  const [monthOffset, setMonthOffset] = useState(0);
  const [kind, setKind] = useState<PlanningKind>('commitments');
  useFocusEffect(useCallback(() => { setToday(financialDate()); }, []));
  useEffect(() => {
    const timer = setInterval(() => setToday(financialDate()), 30000);
    return () => clearInterval(timer);
  }, []);
  const period = monthAtOffset(today, monthOffset);
  const [year, month] = period.split('-');
  const monthLabel = new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric', timeZone: 'America/Argentina/Cordoba' }).format(new Date(`${period}-01T12:00:00Z`));
  return <SafeAreaView style={styles.screen} edges={['top']}>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
      <View style={styles.heading}>
        <Text accessibilityRole="header" style={styles.title}>Movimientos</Text>
        <Text style={styles.help}>Dejá listo cada mes. Confirmá cuando cobrás o pagás.</Text>
      </View>
      <View style={styles.monthNavigation}>
        <Pressable accessibilityRole="button" accessibilityLabel="Mes anterior" disabled={period === '0001-01'} style={styles.monthArrow} onPress={() => setMonthOffset((value) => value - 1)}><Text style={styles.arrowText}>‹</Text></Pressable>
        <Text style={styles.month}>{monthLabel.charAt(0).toUpperCase() + monthLabel.slice(1)}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Mes siguiente" disabled={period === '9999-12'} style={styles.monthArrow} onPress={() => setMonthOffset((value) => value + 1)}><Text style={styles.arrowText}>›</Text></Pressable>
      </View>
      {monthOffset !== 0 && <Pressable accessibilityRole="button" style={styles.monthArrow} onPress={() => setMonthOffset(0)}><Text style={styles.buttonText}>Volver a este mes</Text></Pressable>}
      <View style={styles.navigation}>{([{ value: 'commitments', label: 'Pagos' }, { value: 'income', label: 'Cobros' }] as const).map((option) => <Pressable key={option.value} accessibilityRole="button" accessibilityState={{ selected: kind === option.value }} style={[styles.button, kind === option.value && styles.selected]} onPress={() => setKind(option.value)}><Text style={styles.buttonText}>{option.label}</Text></Pressable>)}</View>
      <PlanningSection key={`${kind}-${year}-${month}`} kind={kind} today={today} period={period} />
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  content: { padding: 20, paddingBottom: 36, gap: 20, maxWidth: 600, width: '100%', alignSelf: 'center' },
  heading: { gap: 10 },
  month: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 17 },
  selected: { borderWidth: 2, borderColor: colors.forest },
  navigation: { flexDirection: 'row', gap: 8 },
  monthNavigation: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  monthArrow: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  arrowText: { color: colors.forest, fontSize: 28 },
  button: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 44, backgroundColor: colors.paleGreen, borderRadius: 12 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 12 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 30 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
});
