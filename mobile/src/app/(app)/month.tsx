import { CalendarDays } from 'lucide-react-native';

import { ComingSoonScreen } from '@/components/ComingSoonScreen';
import { colors } from '@/theme';

export default function MonthScreen() {
  return <ComingSoonScreen title="Tu mes" description="Acá vas a ver ingresos, compromisos y el presupuesto flexible del mes." icon={<CalendarDays color={colors.forest} size={26} />} />;
}
