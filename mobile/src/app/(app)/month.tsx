import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PlanningSection } from '@/planning/PlanningSection';
import { financialDate, monthAtOffset } from '@/planning/validation';
import { colors, fontFamily } from '@/theme';

export default function MonthScreen() {
  const [today, setToday] = useState(financialDate);
  const [monthOffset, setMonthOffset] = useState(0);
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
        <Text accessibilityRole="header" style={styles.title}>Tu mes</Text>
        <Text style={styles.month}>{monthLabel} · Fechas de Argentina</Text>
        <View style={styles.navigation}>
          <Pressable accessibilityRole="button" accessibilityLabel="Mes anterior" disabled={period === '0001-01'} style={styles.button} onPress={() => setMonthOffset((value) => value - 1)}><Text style={styles.buttonText}>‹ Anterior</Text></Pressable>
          <Pressable accessibilityRole="button" style={styles.button} onPress={() => setMonthOffset(0)}><Text style={styles.buttonText}>Este mes</Text></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Mes siguiente" disabled={period === '9999-12'} style={styles.button} onPress={() => setMonthOffset((value) => value + 1)}><Text style={styles.buttonText}>Siguiente ›</Text></Pressable>
        </View>
        <Text style={styles.help}>Ingresos y compromisos del mes seleccionado, junto con los pendientes de meses anteriores.</Text>
        <Text style={styles.help}>Planificá cobros y pagos puntuales o mensuales. No modifican tus saldos. Marcar como recibido o pagado, editar y detener repeticiones queda para otra etapa.</Text>
      </View>
      <PlanningSection key={`income-${year}-${month}`} kind="income" today={today} period={period} />
      <PlanningSection key={`commitments-${year}-${month}`} kind="commitments" today={today} period={period} />
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  content: { padding: 20, paddingBottom: 36, gap: 20, maxWidth: 600, width: '100%', alignSelf: 'center' },
  heading: { gap: 10 },
  month: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 17, textTransform: 'capitalize' },
  navigation: { flexDirection: 'row', gap: 8 },
  button: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 44, backgroundColor: colors.paleGreen, borderRadius: 12 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 12 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 30 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
});
