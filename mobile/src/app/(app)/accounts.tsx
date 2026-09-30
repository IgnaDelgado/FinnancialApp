import { Link, useFocusEffect } from 'expo-router';
import { ArrowLeft, ChevronRight, Plus, RefreshCw, WalletCards } from 'lucide-react-native';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ApiError } from '@/auth/api';
import { useAuth } from '@/auth/AuthProvider';
import {
  createAccount,
  getAccountCashTotals,
  listAccounts,
  updateAccountBalance,
  type AccountCashTotal,
  type AccountType,
  type Currency,
  type FinancialAccount,
} from '@/accounts/api';
import { formatMoney, normalizeMoneyInput } from '@/accounts/format';
import { NoticeBanner } from '@/components/NoticeBanner';
import { colors, fontFamily } from '@/theme';

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: 'CASH', label: 'Efectivo' },
  { value: 'BANK', label: 'Banco' },
  { value: 'DIGITAL_WALLET', label: 'Billetera' },
  { value: 'FOREIGN_CURRENCY', label: 'Moneda extranjera' },
  { value: 'INVESTMENT', label: 'Cuenta de inversión' },
  { value: 'OTHER', label: 'Otra' },
];

const DEFAULT_LIQUID_TYPES: AccountType[] = [
  'CASH', 'BANK', 'DIGITAL_WALLET', 'FOREIGN_CURRENCY',
];

export default function AccountsScreen() {
  const { session, withAccessToken } = useAuth();
  const [accounts, setAccounts] = useState<FinancialAccount[] | null>(null);
  const [cashTotals, setCashTotals] = useState<AccountCashTotal[]>([]);
  const [loading, setLoading] = useState(true);
  const [editor, setEditor] = useState<'create' | 'balance' | null>(null);
  const [selected, setSelected] = useState<FinancialAccount | null>(null);
  const [name, setName] = useState('');
  const [accountType, setAccountType] = useState<AccountType>('BANK');
  const [currency, setCurrency] = useState<Currency>('ARS');
  const [isLiquid, setIsLiquid] = useState(true);
  const [balance, setBalance] = useState('');
  const [isNegative, setIsNegative] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const [accountResult, totalResult] = await withAccessToken((token) =>
      Promise.all([listAccounts(token), getAccountCashTotals(token)]),
    );
    setAccounts(accountResult);
    setCashTotals(totalResult);
  }, [withAccessToken]);

  useFocusEffect(useCallback(() => {
    if (!session) return;
    let active = true;
    setLoading(true);
    void withAccessToken((token) => Promise.all([listAccounts(token), getAccountCashTotals(token)]))
      .then(([accountResult, totalResult]) => { if (active) { setAccounts(accountResult); setCashTotals(totalResult); setError(null); setLoading(false); } })
      .catch((caught) => { if (active) { setError(errorMessage(caught)); setLoading(false); } });
    return () => { active = false; };
  }, [session, withAccessToken]));

  function openCreate() {
    setName('');
    setAccountType('BANK');
    setCurrency(session?.user.reference_currency ?? 'ARS');
    setIsLiquid(true);
    setBalance('');
    setIsNegative(false);
    setSelected(null);
    setEditor('create');
    setError(null);
  }

  function openBalance(account: FinancialAccount) {
    setSelected(account);
    setBalance(account.current_balance.replace(/^-/, ''));
    setIsNegative(account.current_balance.startsWith('-'));
    setEditor('balance');
    setError(null);
  }

  async function save() {
    const normalizedBalance = normalizeMoneyInput(balance);
    if (!normalizedBalance) {
      setError('Ingresá un importe válido, con hasta dos decimales.');
      return;
    }
    const signedBalance = isNegative && !/^0(?:\.0{1,2})?$/.test(normalizedBalance)
      ? `-${normalizedBalance}`
      : normalizedBalance;
    if (editor === 'create' && !name.trim()) {
      setError('Ingresá un nombre para la cuenta.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editor === 'create') {
        await withAccessToken((token) => createAccount(token, {
          name: name.trim(), account_type: accountType, currency,
          initial_balance: signedBalance, is_liquid: isLiquid,
        }));
      } else if (editor === 'balance' && selected) {
        await withAccessToken((token) =>
          updateAccountBalance(token, selected.id, signedBalance),
        );
      }
      await reload();
      setEditor(null);
      setSelected(null);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setSaving(false);
    }
  }

  if (!session) return null;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Link href="/" asChild>
            <Pressable accessibilityLabel="Volver al inicio" style={styles.backButton}>
              <ArrowLeft color={colors.ink} size={20} />
            </Pressable>
          </Link>
          <Text style={styles.title}>Tus cuentas</Text>
          <Pressable accessibilityLabel="Agregar cuenta" onPress={openCreate} style={styles.addButton}>
            <Plus color={colors.white} size={20} />
          </Pressable>
        </View>

        <Text style={styles.intro}>
          Registrá dónde está tu dinero. Las inversiones se cargarán por separado; una cuenta de inversión guarda solo su efectivo.
        </Text>

        {error ? <NoticeBanner message={error} /> : null}

        {editor ? (
          <View style={styles.formCard}>
            <View style={styles.formHeading}>
              <Text style={styles.formTitle}>
                {editor === 'create' ? 'Nueva cuenta' : `Actualizar ${selected?.name ?? 'saldo'}`}
              </Text>
              <Pressable onPress={() => setEditor(null)} style={styles.cancelButton}>
                <Text style={styles.cancelText}>Cancelar</Text>
              </Pressable>
            </View>

            {editor === 'create' ? (
              <>
                <Text style={styles.fieldLabel}>Nombre</Text>
                <TextInput
                  accessibilityLabel="Nombre de la cuenta"
                  autoCapitalize="sentences"
                  maxLength={100}
                  onChangeText={setName}
                  placeholder="Ej. Banco principal"
                  placeholderTextColor={colors.muted}
                  style={styles.input}
                  value={name}
                />
                <Text style={styles.fieldLabel}>Tipo de cuenta</Text>
                <View style={styles.choices}>
                  {ACCOUNT_TYPES.map((option) => (
                    <Pressable
                      accessibilityRole="radio"
                      accessibilityState={{ selected: accountType === option.value }}
                      key={option.value}
                      onPress={() => {
                        setAccountType(option.value);
                        setIsLiquid(DEFAULT_LIQUID_TYPES.includes(option.value));
                      }}
                      style={[styles.choice, accountType === option.value && styles.choiceActive]}
                    >
                      <Text style={[styles.choiceText, accountType === option.value && styles.choiceTextActive]}>
                        {option.label}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                <Text style={styles.fieldLabel}>Moneda</Text>
                <View style={styles.choices}>
                  {(['ARS', 'USD'] as const).map((option) => (
                    <Pressable
                      accessibilityRole="radio"
                      accessibilityState={{ selected: currency === option }}
                      key={option}
                      onPress={() => setCurrency(option)}
                      style={[styles.choice, currency === option && styles.choiceActive]}
                    >
                      <Text style={[styles.choiceText, currency === option && styles.choiceTextActive]}>
                        {option}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </>
            ) : null}

            <Text style={styles.fieldLabel}>
              {editor === 'create' ? 'Saldo actual' : 'Nuevo saldo actual'}
            </Text>
            <TextInput
              accessibilityLabel="Saldo actual"
              keyboardType="decimal-pad"
              onChangeText={(value) => {
                if (value.startsWith('-')) {
                  setIsNegative(true);
                  setBalance(value.slice(1));
                } else {
                  setBalance(value);
                }
              }}
              placeholder="0,00"
              placeholderTextColor={colors.muted}
              style={styles.input}
              value={balance}
            />
            <Pressable
              accessibilityRole="checkbox"
              accessibilityState={{ checked: isNegative }}
              onPress={() => setIsNegative(!isNegative)}
              style={styles.liquidRow}
            >
              <View style={[styles.checkbox, isNegative && styles.checkboxChecked]} />
              <View style={styles.liquidCopy}>
                <Text style={styles.liquidTitle}>Saldo negativo (en rojo)</Text>
                <Text style={styles.liquidDescription}>Activá esta opción si la cuenta debe dinero.</Text>
              </View>
            </Pressable>
            {editor === 'create' ? (
              <Pressable
                accessibilityRole="checkbox"
                accessibilityState={{ checked: isLiquid }}
                onPress={() => setIsLiquid(!isLiquid)}
                style={styles.liquidRow}
              >
                <View style={[styles.checkbox, isLiquid && styles.checkboxChecked]} />
                <View style={styles.liquidCopy}>
                  <Text style={styles.liquidTitle}>Disponible para gastos</Text>
                  <Text style={styles.liquidDescription}>Desactivá esta opción para dinero que no querés usar en gastos.</Text>
                </View>
              </Pressable>
            ) : (
              <Text style={styles.helpText}>Ingresá el saldo completo que figura hoy, no la diferencia respecto del anterior.</Text>
            )}
            <Pressable disabled={saving} onPress={() => void save()} style={styles.saveButton}>
              {saving ? <ActivityIndicator color={colors.white} /> : (
                <Text style={styles.saveText}>{editor === 'create' ? 'Guardar cuenta' : 'Guardar saldo'}</Text>
              )}
            </Pressable>
          </View>
        ) : null}

        {loading && accounts === null ? (
          <ActivityIndicator color={colors.forest} style={styles.loading} />
        ) : accounts === null ? (
          <Pressable onPress={() => void reload().catch((caught) => setError(errorMessage(caught)))} style={styles.emptyAction}>
            <Text style={styles.emptyActionText}>Reintentar</Text>
          </Pressable>
        ) : accounts.length === 0 ? (
          <View style={styles.emptyCard}>
            <WalletCards color={colors.forest} size={27} />
            <Text style={styles.emptyTitle}>Empezá por una cuenta</Text>
            <Text style={styles.emptyCopy}>Puede ser efectivo, banco o billetera. Después podrás ver tus saldos organizados por moneda.</Text>
            {!editor ? <Pressable onPress={openCreate} style={styles.emptyAction}><Text style={styles.emptyActionText}>Agregar cuenta</Text></Pressable> : null}
          </View>
        ) : (
          <View style={styles.list}>
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Saldo total de cuentas</Text>
              {cashTotals.map((total) => (
                <Text
                  key={total.currency}
                  style={[styles.summaryAmount, total.balance.startsWith('-') && styles.negativeBalance]}
                >
                  {formatMoney(total.balance, total.currency)}
                </Text>
              ))}
              <Text style={styles.summaryHelp}>
                Suma saldos positivos y negativos por moneda. No es el dinero disponible para gastar ni el patrimonio neto.
              </Text>
            </View>
            <Text style={styles.sectionTitle}>Cuentas activas</Text>
            {accounts.map((account) => (
              <Pressable key={account.id} onPress={() => openBalance(account)} style={styles.accountCard}>
                <View style={styles.accountIcon}><WalletCards color={colors.forest} size={20} /></View>
                <View style={styles.accountCopy}>
                  <Text style={styles.accountName}>{account.name}</Text>
                  <Text style={styles.accountMeta}>
                    {ACCOUNT_TYPES.find((item) => item.value === account.account_type)?.label} · {account.current_balance.startsWith('-') ? 'Saldo en rojo' : account.is_liquid ? 'Cuenta líquida' : 'No líquida'}
                  </Text>
                </View>
                <View style={styles.accountEnd}>
                  <Text style={[styles.accountBalance, account.current_balance.startsWith('-') && styles.negativeBalance]}>{formatMoney(account.current_balance, account.currency)}</Text>
                  <RefreshCw color={colors.muted} size={14} />
                </View>
                <ChevronRight color={colors.muted} size={16} />
              </Pressable>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function errorMessage(caught: unknown): string {
  return caught instanceof ApiError ? caught.message : 'No pudimos completar la acción.';
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  content: { gap: 16, paddingBottom: 34, paddingHorizontal: 20, paddingTop: 14 },
  header: { alignItems: 'center', flexDirection: 'row', gap: 12 },
  backButton: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 15, height: 44, justifyContent: 'center', width: 44 },
  title: { color: colors.ink, flex: 1, fontFamily: fontFamily.displayBold, fontSize: 25 },
  addButton: { alignItems: 'center', backgroundColor: colors.forest, borderRadius: 15, height: 44, justifyContent: 'center', width: 44 },
  intro: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
  loading: { marginTop: 45 },
  formCard: { backgroundColor: colors.white, borderColor: colors.line, borderRadius: 22, borderWidth: 1, gap: 10, padding: 17 },
  formHeading: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  formTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 19 },
  cancelButton: { padding: 8 },
  cancelText: { color: colors.muted, fontFamily: fontFamily.semibold, fontSize: 12 },
  fieldLabel: { color: colors.slate, fontFamily: fontFamily.semibold, fontSize: 12, marginTop: 8 },
  input: { backgroundColor: colors.field, borderColor: colors.line, borderRadius: 13, borderWidth: 1, color: colors.ink, fontFamily: fontFamily.body, fontSize: 16, minHeight: 50, paddingHorizontal: 13 },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  choice: { backgroundColor: colors.field, borderColor: colors.line, borderRadius: 11, borderWidth: 1, minHeight: 38, paddingHorizontal: 11, paddingVertical: 9 },
  choiceActive: { backgroundColor: colors.paleGreen, borderColor: colors.forest },
  choiceText: { color: colors.slate, fontFamily: fontFamily.medium, fontSize: 12 },
  choiceTextActive: { color: colors.forest, fontFamily: fontFamily.bold },
  liquidRow: { alignItems: 'center', flexDirection: 'row', gap: 10, minHeight: 58 },
  checkbox: { borderColor: colors.forest, borderRadius: 5, borderWidth: 2, height: 20, width: 20 },
  checkboxChecked: { backgroundColor: colors.forest },
  liquidCopy: { flex: 1 },
  liquidTitle: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  liquidDescription: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 11, lineHeight: 16 },
  helpText: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 12, lineHeight: 18 },
  saveButton: { alignItems: 'center', backgroundColor: colors.forest, borderRadius: 15, justifyContent: 'center', minHeight: 52, marginTop: 5 },
  saveText: { color: colors.white, fontFamily: fontFamily.bold, fontSize: 14 },
  emptyCard: { alignItems: 'flex-start', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 20, borderWidth: 1, gap: 8, padding: 20 },
  emptyTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 20 },
  emptyCopy: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 13, lineHeight: 20 },
  emptyAction: { backgroundColor: colors.paleGreen, borderRadius: 12, marginTop: 6, minHeight: 44, paddingHorizontal: 14, paddingVertical: 12 },
  emptyActionText: { color: colors.forest, fontFamily: fontFamily.bold, fontSize: 13 },
  list: { gap: 10 },
  summaryCard: { backgroundColor: colors.paleGreen, borderRadius: 20, gap: 5, padding: 18 },
  summaryTitle: { color: colors.slate, fontFamily: fontFamily.semibold, fontSize: 13 },
  summaryAmount: { color: colors.forestDeep, fontFamily: fontFamily.displayBold, fontSize: 24 },
  summaryHelp: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 11, lineHeight: 16, marginTop: 4 },
  negativeBalance: { color: colors.coral },
  sectionTitle: { color: colors.ink, fontFamily: fontFamily.displayMedium, fontSize: 17 },
  accountCard: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.line, borderRadius: 18, borderWidth: 1, flexDirection: 'row', gap: 9, minHeight: 78, padding: 12 },
  accountIcon: { alignItems: 'center', backgroundColor: colors.paleGreen, borderRadius: 12, height: 40, justifyContent: 'center', width: 40 },
  accountCopy: { flex: 1, gap: 3 },
  accountName: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 13 },
  accountMeta: { color: colors.muted, fontFamily: fontFamily.body, fontSize: 10.5 },
  accountEnd: { alignItems: 'flex-end', gap: 5 },
  accountBalance: { color: colors.ink, fontFamily: fontFamily.semibold, fontSize: 12 },
});
