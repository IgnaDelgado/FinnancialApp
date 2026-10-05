import { File, Paths } from 'expo-file-system';
import { isAvailableAsync, shareAsync } from 'expo-sharing';

export async function saveExport(json: string): Promise<void> {
  if (!await isAvailableAsync()) throw new Error('Este dispositivo no permite compartir archivos.');
  const file = new File(Paths.cache, `financial-plan-${Date.now()}.json`);
  try {
    file.create();
    file.write(json);
    await shareAsync(file.uri, { mimeType: 'application/json', UTI: 'public.json', dialogTitle: 'Guardar mis datos' });
  } finally {
    if (file.exists) file.delete();
  }
}
