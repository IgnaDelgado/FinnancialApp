import { LinearGradient } from 'expo-linear-gradient';
import { useFocusEffect } from 'expo-router';
import { Sparkles } from 'lucide-react-native';
import { useCallback, useMemo, useRef } from 'react';
import {
  AccessibilityInfo,
  Animated,
  Easing,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
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
  const entrance = useMemo(() => new Animated.Value(0), []);
  const drift = useMemo(() => new Animated.Value(0), []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      let floating: Animated.CompositeAnimation | null = null;
      scrollRef.current?.scrollTo({ animated: false, y: 0 });

      void AccessibilityInfo.isReduceMotionEnabled().then((reduceMotion) => {
        if (!active) return;
        entrance.setValue(reduceMotion ? 1 : 0);
        drift.setValue(0);

        if (reduceMotion) return;

        Animated.timing(entrance, {
          duration: 620,
          easing: Easing.out(Easing.cubic),
          toValue: 1,
          useNativeDriver: true,
        }).start();

        floating = Animated.loop(
          Animated.sequence([
            Animated.timing(drift, {
              duration: 3200,
              easing: Easing.inOut(Easing.sin),
              toValue: 1,
              useNativeDriver: true,
            }),
            Animated.timing(drift, {
              duration: 3200,
              easing: Easing.inOut(Easing.sin),
              toValue: 0,
              useNativeDriver: true,
            }),
          ]),
        );
        floating.start();
      });

      return () => {
        active = false;
        floating?.stop();
      };
    }, [drift, entrance]),
  );

  const translateY = entrance.interpolate({ inputRange: [0, 1], outputRange: [24, 0] });
  const opacity = entrance.interpolate({ inputRange: [0, 1], outputRange: [0.32, 1] });
  const blobY = drift.interpolate({ inputRange: [0, 1], outputRange: [-8, 10] });
  const blobX = drift.interpolate({ inputRange: [0, 1], outputRange: [0, -9] });

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <LinearGradient colors={['#FFF8F2', '#F2FAF7', '#F1F2FF']} style={styles.flex}>
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
            <View pointerEvents="none" style={styles.decorations}>
              <Animated.View style={[styles.blob, styles.blobMint, { transform: [{ translateY: blobY }] }]} />
              <Animated.View style={[styles.blob, styles.blobPeach, { transform: [{ translateX: blobX }] }]} />
              <View style={[styles.blob, styles.blobLavender]} />
            </View>

            <Animated.View style={[styles.header, { opacity, transform: [{ translateY }] }]}>
              <BrandMark />
              <View style={styles.eyebrowPill}>
                <Sparkles color={colors.lavenderDeep} size={14} />
                <Text style={styles.eyebrow}>{eyebrow}</Text>
              </View>
              <Text style={styles.title}>{title}</Text>
              <Text style={styles.subtitle}>{subtitle}</Text>
            </Animated.View>

            <Animated.View
              style={[
                styles.card,
                {
                  opacity,
                  transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [38, 0] }) }],
                },
              ]}
            >
              {children}
            </Animated.View>

            <View style={styles.footer}>
              <View style={styles.footerDot} />
              <Text style={styles.footerText}>Un plan simple para sentirte más tranquilo con tu dinero.</Text>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safeArea: { backgroundColor: '#FFF8F2', flex: 1 },
  scrollContent: { flexGrow: 1, paddingBottom: 30, paddingHorizontal: 18 },
  decorations: { bottom: 0, left: 0, overflow: 'hidden', position: 'absolute', right: 0, top: 0 },
  blob: { position: 'absolute' },
  blobMint: {
    backgroundColor: colors.mintBright,
    borderRadius: 95,
    height: 190,
    opacity: 0.36,
    right: -68,
    top: 60,
    width: 190,
  },
  blobPeach: {
    backgroundColor: colors.peach,
    borderRadius: 80,
    height: 160,
    left: -90,
    opacity: 0.35,
    top: 245,
    width: 160,
  },
  blobLavender: {
    backgroundColor: colors.lavender,
    borderRadius: 70,
    height: 140,
    opacity: 0.28,
    right: -72,
    top: 520,
    width: 140,
  },
  header: { paddingHorizontal: 8, paddingTop: 12 },
  eyebrowPill: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.76)',
    borderColor: 'rgba(107,101,167,0.14)',
    borderRadius: 999,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 7,
    marginTop: 34,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  eyebrow: { color: colors.lavenderDeep, fontFamily: fontFamily.bold, fontSize: 9, letterSpacing: 0.9 },
  title: {
    color: colors.ink,
    fontFamily: fontFamily.displayBold,
    fontSize: 38,
    letterSpacing: -1.15,
    lineHeight: 42,
    marginTop: 13,
    maxWidth: 340,
  },
  subtitle: {
    color: colors.muted,
    fontFamily: fontFamily.body,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 9,
    maxWidth: 335,
  },
  card: {
    backgroundColor: 'rgba(255,255,255,0.94)',
    borderColor: 'rgba(255,255,255,0.95)',
    borderRadius: 30,
    borderWidth: 1,
    marginTop: 24,
    padding: 22,
    shadowColor: colors.shadow,
    shadowOffset: { height: 14, width: 0 },
    shadowOpacity: 0.09,
    shadowRadius: 30,
  },
  footer: { alignItems: 'center', flexDirection: 'row', gap: 8, justifyContent: 'center', marginTop: 22, paddingHorizontal: 20 },
  footerDot: { backgroundColor: colors.mint, borderRadius: 4, height: 7, width: 7 },
  footerText: { color: colors.muted, flexShrink: 1, fontFamily: fontFamily.medium, fontSize: 10.5, textAlign: 'center' },
});
