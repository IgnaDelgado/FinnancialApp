import Animated, {
  FadeInDown,
  ReduceMotion,
} from 'react-native-reanimated';
import {
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

const screenEntrance = FadeInDown.duration(420).reduceMotion(ReduceMotion.System);

export function AuthShell({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
}) {
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView
          bounces={false}
          contentContainerStyle={styles.content}
          keyboardDismissMode="interactive"
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Animated.View entering={screenEntrance} style={styles.screen}>
            <View style={styles.header}>
              <BrandMark />
              <Text style={styles.title}>{title}</Text>
            </View>
            <View style={styles.form}>{children}</View>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  content: {
    alignItems: 'center',
    flexGrow: 1,
    paddingBottom: 24,
    paddingHorizontal: 24,
    paddingTop: 56,
  },
  screen: { maxWidth: 440, width: '100%' },
  header: { gap: 24, marginBottom: 26 },
  form: { gap: 14 },
  title: {
    color: colors.ink,
    fontFamily: fontFamily.displayBold,
    fontSize: 30,
    lineHeight: 36,
  },
});
