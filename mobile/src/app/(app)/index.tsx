import { Link, useFocusEffect } from 'expo-router';
import { ArrowDownLeft, ArrowUpRight, ChevronRight, RefreshCw, WalletCards } from 'lucide-react-native';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { formatMoney } from '@/accounts/format';
import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import { BrandMark } from '@/components/BrandMark';
import { FormField } from '@/components/FormField';
import { NoticeBanner } from '@/components/NoticeBanner';
import { getHomeSnapshot, type HomeSnapshot } from '@/home/api';
import { previewExpense } from '@/home/preview';
import { displayFinancialDate, financialDate } from '@/planning/validation';
import { colors, fontFamily } from '@/theme';

export default function HomeScreen() {
  const { session, isBootstrapping, withAccessToken } = useAuth();
  const [snapshot, setSnapshot] = useState<HomeSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCurrency, setCurrency] = useState<'ARS' | 'USD' | null>(null);
  const currency = selectedCurrency ?? session?.user.reference_currency ?? 'ARS';
  const [revision, setRevision] = useState(0);
  const [details, setDetails] = useState(false);
  const [expense, setExpense] = useState('');
  const authenticated = useRef(withAccessToken);
  useEffect(() => { authenticated.current = withAccessToken; }, [withAccessToken]);
  const ownerId = session?.user.id;
  const [today, setToday] = useState(financialDate);
  useEffect(() => { const timer = setInterval(() => setToday(financialDate()), 30000); return () => clearInterval(timer); }, []);
  useFocusEffect(useCallback(() => {
    void revision;
    void today;
    let active = true;
    setSnapshot(null); setError(null); setExpense('');
    if (isBootstrapping || !ownerId) return () => { active = false; };
    void authenticated.current(getHomeSnapshot).then((result) => {
      if (active) setSnapshot(result);
    }).catch((caught: unknown) => {
      if (active) setError(caught instanceof ApiError ? caught.message : 'No pudimos cargar tu resumen.');
    });
    return () => { active = false; };
  }, [ownerId, isBootstrapping, revision, today]));
  const flow = snapshot?.currencies.find((item) => item.currency === currency);
  const preview = flow && expense ? previewExpense(flow.cash_after_bills, expense) : null;
  const shortfall = flow?.cash_after_bills.startsWith('-');
  const empty = snapshot?.account_count === 0;

  return <SafeAreaView style={styles.screen} edges={['top']}>
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.top}><BrandMark /><Pressable accessibilityRole="button" accessibilityLabel="Actualizar resumen" style={styles.iconButton} onPress={() => setRevision((value) => value + 1)}><RefreshCw size={19} color={colors.forest} /></Pressable></View>
      <Text style={styles.eyebrow}>MENOS CUENTAS MENTALES</Text>
      <Text accessibilityRole="header" style={styles.title}>Tu mes, más claro.</Text>
      <Text style={styles.subtitle}>Lo que tenés. Lo que viene. Lo que te queda.</Text>

      {error ? <View style={styles.card}><NoticeBanner message={error} /><Pressable accessibilityRole="button" style={styles.button} onPress={() => setRevision((value) => value + 1)}><Text style={styles.buttonText}>Volver a intentar</Text></Pressable></View> : !snapshot ? <ActivityIndicator accessibilityLabel="Cargando resumen" color={colors.forest} style={styles.loading} /> : <>
        {empty ? <View style={styles.welcome}>
          <View style={styles.heroIcon}><WalletCards color={colors.forest} size={28} /></View>
          <Text style={styles.cardTitle}>Empezá por lo que ya sabés.</Text>
          <Text style={styles.body}>¿Cuánto tenés hoy y qué pagos grandes te esperan? Con eso armamos tu primera foto del mes.</Text>
          <Link href="/accounts" asChild><Pressable accessibilityRole="button" style={styles.primary}><Text style={styles.primaryText}>1. Agregar mi dinero</Text><ChevronRight color={colors.white} size={18} /></Pressable></Link>
          <Text style={styles.small}>Después sumás alquiler, servicios o tarjeta. No hace falta anotar cada café.</Text>
        </View> : flow && <>
          <View style={styles.currencyRow}>{(['ARS', 'USD'] as const).map((unit) => <Pressable key={unit} accessibilityRole="button" accessibilityState={{ selected: currency === unit }} style={[styles.currency, currency === unit && styles.currencySelected]} onPress={() => { setCurrency(unit); setExpense(''); }}><Text style={[styles.currencyText, currency === unit && styles.currencyTextSelected]}>{unit === 'ARS' ? 'Pesos' : 'Dólares'}</Text></Pressable>)}</View>
          <View style={[styles.hero, shortfall && styles.heroShortfall]}>
            <Text style={styles.heroLabel}>{shortfall ? 'FALTARÍA PARA CUBRIR TUS PAGOS' : 'DESPUÉS DE TUS PAGOS PENDIENTES'}</Text>
            <Text style={styles.heroValue}>{formatMoney(flow.cash_after_bills, currency)}</Text>
            <Text style={styles.heroCopy}>Con los saldos y pagos que registraste hasta el {displayFinancialDate(snapshot.month_end)}.</Text>
            <View style={styles.heroDivider} />
            <Text style={styles.heroFoot}>Todavía tenés que separar tus gastos del día a día y tus ahorros. Este margen no es un límite seguro de gasto.</Text>
          </View>
          <View style={styles.breakdown}>
            <Link href="/accounts" asChild><Pressable accessibilityRole="button" style={styles.line}><View style={styles.lineIcon}><WalletCards color={colors.forest} size={18} /></View><View style={styles.grow}><Text style={styles.lineTitle}>Dinero de uso diario</Text><Text style={styles.small}>Saldos positivos que podés usar</Text></View><Text style={styles.lineAmount}>{formatMoney(flow.liquid_cash, currency)}</Text></Pressable></Link>
            <Link href="/month" asChild><Pressable accessibilityRole="button" style={styles.line}><View style={styles.lineIcon}><ArrowUpRight color={colors.peachDeep} size={18} /></View><View style={styles.grow}><Text style={styles.lineTitle}>Pagos pendientes</Text><Text style={styles.small}>Hasta fin de mes, incluidos vencidos</Text></View><Text style={styles.lineAmount}>{formatMoney(flow.pending_bills, currency)}</Text></Pressable></Link>
            <Link href="/month" asChild><Pressable accessibilityRole="button" style={styles.line}><View style={styles.lineIcon}><ArrowDownLeft color={colors.forest} size={18} /></View><View style={styles.grow}><Text style={styles.lineTitle}>Por cobrar</Text><Text style={styles.small}>Desde hoy hasta fin de mes</Text></View><Text style={styles.lineAmount}>{formatMoney(flow.expected_income, currency)}</Text></Pressable></Link>
          </View>
          <View style={styles.forecast}><Text style={styles.lineTitle}>Si cobrás lo previsto</Text><Text style={styles.forecastValue}>{formatMoney(flow.forecast_after_bills, currency)}</Text><Text style={styles.small}>Proyección después de pagos. Ese ingreso todavía no está en tus cuentas.</Text></View>
          {flow.negative_balances.startsWith('-') && <NoticeBanner message={`Además tenés saldos en rojo por ${formatMoney(flow.negative_balances, currency)}. No están descontados del margen.`} />}
          {flow.overdue_income_count > 0 && <NoticeBanner message={`${flow.overdue_income_count} ingreso(s) con fecha pasada siguen pendientes. No los contamos como dinero por cobrar este mes.`} />}
          {snapshot.commitment_count === 0 && <Link href="/month" asChild><Pressable accessibilityRole="button" style={styles.nudge}><Text style={styles.lineTitle}>Completá la foto con tus pagos fijos</Text><Text style={styles.body}>Agregá alquiler, servicios o tarjeta una sola vez y repetilos cada mes.</Text><Text style={styles.linkText}>Agregar mis pagos →</Text></Pressable></Link>}
          <View style={styles.card}>
            <Text accessibilityRole="header" style={styles.cardTitle}>¿Y si gasto esto?</Text>
            <Text style={styles.body}>Probá una compra antes de decidir. Nada se guarda.</Text>
            <FormField icon={null} label={`Importe en ${currency}`} value={expense} onChangeText={setExpense} keyboardType="decimal-pad" placeholder="Ej.: 25000" />
            {expense.length > 0 && (preview === null ? <Text accessibilityRole="alert" style={styles.small}>Ingresá un importe mayor que cero, con hasta dos decimales y sin puntos de miles.</Text> : <View accessibilityLiveRegion="polite" style={styles.result}><Text style={styles.small}>Margen después de esa compra</Text><Text style={[styles.resultValue, preview.startsWith('-') && styles.negative]}>{formatMoney(preview, currency)}</Text><Text style={styles.body}>{preview.startsWith('-') ? 'La compra dejaría un faltante para los pagos registrados.' : 'De ese margen todavía salen tus gastos diarios y ahorros.'}</Text></View>)}
          </View>
          <Pressable accessibilityRole="button" accessibilityState={{ expanded: details }} style={styles.disclosure} onPress={() => setDetails(!details)}><Text style={styles.linkText}>{details ? 'Cerrar explicación' : '¿De dónde sale este número?'}</Text></Pressable>
          {details && <View style={styles.card}><Text style={styles.body}>Sumamos todos los saldos positivos de cuentas activas marcadas para uso diario y restamos los pagos pendientes hasta fin de mes. Los ingresos previstos aparecen sólo en la proyección.</Text><Text style={styles.body}>Las cuentas para inversión o no disponibles, los saldos negativos, presupuestos y objetivos no se restan de este margen. Pesos y dólares se muestran separados.</Text><Text style={styles.small}>Confirmá los pagos e ingresos en Movimientos cuando ocurran. Si ya actualizaste el saldo para incluirlos, elegí «Ya estaba incluido en el saldo» para no contarlos dos veces.</Text></View>}
        </>}
        <View style={styles.actions}><Link href="/accounts" asChild><Pressable accessibilityRole="button" style={styles.action}><WalletCards color={colors.forest} size={21} /><Text style={styles.lineTitle}>{empty ? 'Mi dinero' : 'Actualizar mi dinero'}</Text><Text style={styles.small}>Efectivo, banco y billetera</Text></Pressable></Link><Link href="/month" asChild><Pressable accessibilityRole="button" style={styles.action}><ArrowUpRight color={colors.forest} size={21} /><Text style={styles.lineTitle}>Organizar mis pagos</Text><Text style={styles.small}>Y lo que espero cobrar</Text></Pressable></Link></View>
        <Text style={styles.footer}>Una revisión cuando cambie tu saldo. Tus pagos mensuales se repiten solos.</Text>
      </>}
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  content: { padding: 20, paddingBottom: 35, gap: 16, maxWidth: 600, width: '100%', alignSelf: 'center' },
  top: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  iconButton: { minHeight: 44, minWidth: 44, alignItems: 'center', justifyContent: 'center' },
  eyebrow: { color: colors.green, fontFamily: fontFamily.bold, fontSize: 10, letterSpacing: 1.5, marginTop: 12 },
  title: { color: colors.ink, fontFamily: fontFamily.displayBold, fontSize: 34, letterSpacing: -1 },
  subtitle: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 15, marginTop: -8 },
  loading: { marginVertical: 60 },
  card: { borderRadius: 22, backgroundColor: colors.white, padding: 20, gap: 12, borderColor: colors.line, borderWidth: 1 },
  welcome: { borderRadius: 26, backgroundColor: colors.softMint, padding: 24, gap: 16 },
  heroIcon: { backgroundColor: colors.white, width: 54, height: 54, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  cardTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 23 },
  body: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 14, lineHeight: 21 },
  small: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18 },
  primary: { backgroundColor: colors.forest, padding: 16, minHeight: 52, borderRadius: 15, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  primaryText: { color: colors.white, fontFamily: fontFamily.semibold, fontSize: 15 },
  currencyRow: { flexDirection: 'row', gap: 8 },
  currency: { minHeight: 44, paddingHorizontal: 20, borderRadius: 14, justifyContent: 'center', backgroundColor: colors.white, borderWidth: 1, borderColor: colors.line },
  currencySelected: { backgroundColor: colors.forest, borderColor: colors.forest },
  currencyText: { color: colors.muted, fontFamily: fontFamily.semibold, fontSize: 13 },
  currencyTextSelected: { color: colors.white },
  hero: { backgroundColor: colors.forestDeep, borderRadius: 26, padding: 24, gap: 12 },
  heroShortfall: { backgroundColor: '#693F36' },
  heroLabel: { color: colors.mintBright, fontFamily: fontFamily.bold, fontSize: 10, letterSpacing: 1 },
  heroValue: { color: colors.white, fontFamily: fontFamily.displayBold, fontSize: 31, letterSpacing: -1 },
  heroCopy: { color: '#D1E4DE', fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
  heroDivider: { height: 1, backgroundColor: '#527069' },
  heroFoot: { color: '#D1E4DE', fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18 },
  breakdown: { backgroundColor: colors.white, borderRadius: 22, paddingHorizontal: 15, borderWidth: 1, borderColor: colors.line },
  line: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 16 },
  lineIcon: { backgroundColor: colors.canvas, borderRadius: 12, padding: 8 },
  grow: { flex: 1 },
  lineTitle: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  lineAmount: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 12, flexShrink: 1, maxWidth: '42%' },
  forecast: { backgroundColor: colors.softMint, padding: 20, borderRadius: 20, gap: 7 },
  forecastValue: { color: colors.forest, fontFamily: fontFamily.displayMedium, fontSize: 25 },
  nudge: { borderRadius: 20, backgroundColor: colors.paleYellow, padding: 20, gap: 10 },
  linkText: { color: colors.forest, fontFamily: fontFamily.semibold, fontSize: 13 },
  result: { backgroundColor: colors.canvas, borderRadius: 15, padding: 16, gap: 7 },
  resultValue: { color: colors.forest, fontFamily: fontFamily.displayMedium, fontSize: 26 },
  negative: { color: colors.peachDeep },
  disclosure: { minHeight: 44, justifyContent: 'center', alignItems: 'center' },
  actions: { flexDirection: 'row', gap: 10 },
  action: { flex: 1, backgroundColor: colors.white, borderRadius: 18, borderWidth: 1, borderColor: colors.line, padding: 16, gap: 10, minHeight: 130 },
  footer: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18, textAlign: 'center' },
  button: { padding: 14, minHeight: 44 },
  buttonText: { color: colors.forest, fontFamily: fontFamily.semibold },
});
