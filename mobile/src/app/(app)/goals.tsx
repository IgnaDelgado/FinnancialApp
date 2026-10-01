import { Target } from 'lucide-react-native';

import { ComingSoonScreen } from '@/components/ComingSoonScreen';
import { colors } from '@/theme';

export default function GoalsScreen() {
  return <ComingSoonScreen title="Objetivos" description="Acá vas a organizar tus metas y el dinero asignado a cada una." icon={<Target color={colors.forest} size={26} />} />;
}
