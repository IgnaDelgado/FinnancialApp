import { Redirect } from 'expo-router';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { colors } from '@/theme';

export default function IndexRoute() {
  const { isBootstrapping, session } = useAuth();

  if (isBootstrapping) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color={colors.mint} size="large" />
      </View>
    );
  }

  return <Redirect href={session ? '/(app)' : '/(auth)/login'} />;
}

const styles = StyleSheet.create({
  loading: {
    alignItems: 'center',
    backgroundColor: colors.forestDeep,
    flex: 1,
    justifyContent: 'center',
  },
});
