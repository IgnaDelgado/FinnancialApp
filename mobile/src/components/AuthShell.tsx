import { useFocusEffect } from 'expo-router';
import { useCallback, useRef } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BrandMark } from '@/components/BrandMark';
import { colors, fontFamily } from '@/theme';

export function AuthShell({
  children,
  eyebrow,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  eyebrow: string;
  title: string;
  subtitle: string;
}) {
  const scrollRef = useRef<ScrollView>(null);

  useFocusEffect(
    useCallback(() => {
      scrollRef.current?.scrollTo({ animated: false, y: 0 });
    }, []),
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          ref={scrollRef}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.hero}>
            <View pointerEvents="none" style={styles.orbOne} />
            <View pointerEvents="none" style={styles.orbTwo} />
            <BrandMark inverted />
            <Text style={styles.eyebrow}>{eyebrow}</Text>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.subtitle}>{subtitle}</Text>
          </View>
          <View style={styles.card}>{children}</View>
          <Text style={styles.footer}>Planificá con claridad. Decidí con confianza.</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safeArea: { backgroundColor: colors.forestDeep, flex: 1 },
  scrollContent: { backgroundColor: colors.canvas, flexGrow: 1, paddingBottom: 28 },
  hero: {
    backgroundColor: colors.forestDeep,
    minHeight: 310,
    overflow: 'hidden',
    paddingHorizontal: 24,
    paddingTop: 20,
  },
  orbOne: {
    backgroundColor: 'rgba(216,243,107,0.09)',
    borderRadius: 120,
    height: 210,
    position: 'absolute',
    right: -76,
    top: -48,
    width: 210,
  },
  orbTwo: {
    borderColor: 'rgba(255,255,255,0.08)',
    borderRadius: 100,
    borderWidth: 28,
    height: 176,
    position: 'absolute',
    right: 22,
    top: 92,
    width: 176,
  },
  eyebrow: {
    color: colors.mint,
    fontFamily: fontFamily.bold,
    fontSize: 10,
    letterSpacing: 1.25,
    marginTop: 48,
  },
  title: {
    color: colors.white,
    fontFamily: fontFamily.displayBold,
    fontSize: 38,
    letterSpacing: -1,
    lineHeight: 42,
    marginTop: 8,
    maxWidth: 310,
  },
  subtitle: {
    color: '#C6D3CE',
    fontFamily: fontFamily.body,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 10,
    maxWidth: 320,
  },
  card: {
    backgroundColor: colors.canvas,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    marginTop: -28,
    paddingHorizontal: 24,
    paddingTop: 28,
  },
  footer: {
    color: colors.muted,
    fontFamily: fontFamily.medium,
    fontSize: 11,
    marginTop: 24,
    textAlign: 'center',
  },
});
