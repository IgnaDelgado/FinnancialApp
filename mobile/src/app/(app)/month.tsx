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
        <Text accessibilityRole="header" style={styles.title}>Mi plan</Text>
        <Text style={styles.month}>{monthLabel.charAt(0).toUpperCase() + monthLabel.slice(1)}</Text>
        <View style={styles.navigation}>
          <Pressable accessibilityRole="button" accessibilityLabel="Mes anterior" disabled={period === '0001-01'} style={styles.button} onPress={() => setMonthOffset((value) => value - 1)}><Text style={styles.buttonText}>‹ Anterior</Text></Pressable>
          <Pressable accessibilityRole="button" style={styles.button} onPress={() => setMonthOffset(0)}><Text style={styles.buttonText}>Este mes</Text></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Mes siguiente" disabled={period === '9999-12'} style={styles.button} onPress={() => setMonthOffset((value) => value + 1)}><Text style={styles.buttonText}>Siguiente ›</Text></Pressable>
        </View>
        <Text style={styles.help}>Anotá los pagos importantes y lo que esperás cobrar. Los mensuales se repiten solos.</Text>
        <Text style={styles.help}>Los planes no cambian tus saldos hasta que confirmás un cobro o pago. Si ya estaba incluido, podés confirmarlo sin cambiar el saldo.</Text>
      </View>
      <View style={styles.navigation}>{([{ value: 'commitments', label: 'Lo que pago' }, { value: 'income', label: 'Lo que cobro' }] as const).map((option) => <Pressable key={option.value} accessibilityRole="button" accessibilityState={{ selected: kind === option.value }} style={[styles.button, kind === option.value && styles.selected]} onPress={() => setKind(option.value)}><Text style={styles.buttonText}>{option.label}</Text></Pressable>)}</View>
      <PlanningSection key={`${kind}-${year}-${month}`} kind={kind} today={today} period={period} />
      <Text style={styles.help}>Confirmá cuando ocurra el cobro o pago. Editar, deshacer confirmaciones y detener repeticiones todavía no está disponible.</Text>
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
  button: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 44, backgroundColor: colors.paleGreen, borderRadius: 12 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 12 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 30 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
});
