import { ChartNoAxesCombined } from 'lucide-react-native';

import { ComingSoonScreen } from '@/components/ComingSoonScreen';
import { colors } from '@/theme';

export default function InvestmentsScreen() {
  return <ComingSoonScreen title="Inversiones" description="Acá vas a seguir tus posiciones y sus valores cargados manualmente." icon={<ChartNoAxesCombined color={colors.forest} size={26} />} />;
}
