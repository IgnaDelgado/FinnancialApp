import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PlanningSection } from '@/planning/PlanningSection';
import { financialDate } from '@/planning/validation';
import { colors, fontFamily } from '@/theme';

export default function MonthScreen() {
  const [today, setToday] = useState(financialDate);
  useFocusEffect(useCallback(() => { setToday(financialDate()); }, []));
  useEffect(() => {
    const timer = setInterval(() => setToday(financialDate()), 30000);
    return () => clearInterval(timer);
  }, []);
  const [year, month] = today.split('-');
  return <SafeAreaView style={styles.screen} edges={['top']}>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
      <View style={styles.heading}>
        <Text accessibilityRole="header" style={styles.title}>Tu mes</Text>
        <Text style={styles.help}>{month}/{year} · Fechas de Argentina</Text>
        <Text style={styles.help}>Ingresos y compromisos del mes, junto con todos los pendientes de meses anteriores.</Text>
        <Text style={styles.help}>Este es tu primer registro de planificación. Marcar como recibido o pagado y modificar registros quedará para otra etapa.</Text>
      </View>
      <PlanningSection key={`income-${year}-${month}`} kind="income" today={today} />
      <PlanningSection key={`commitments-${year}-${month}`} kind="commitments" today={today} />
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  content: { padding: 20, paddingBottom: 36, gap: 20, maxWidth: 600, width: '100%', alignSelf: 'center' },
  heading: { gap: 10 },
  title: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 30 },
  help: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
});
