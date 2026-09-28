# Curso práctico: React Native, Expo y autenticación

Este documento explica la aplicación móvil de Financial Plan desde cero. La
meta no es memorizar archivos, sino entender cómo viajan los datos desde un
campo de texto hasta FastAPI y cómo regresan a la interfaz.

## 1. El mapa tecnológico

- **JavaScript** es el lenguaje que se ejecuta.
- **TypeScript** agrega tipos durante el desarrollo. Al compilar, esos tipos se
  eliminan; no validan por sí solos el JSON recibido.
- **React** permite describir la interfaz como una función del estado.
- **React Native** traduce componentes como `View`, `Text` y `Pressable` a
  controles nativos de Android y iOS.
- **Expo** proporciona el entorno, CLI, módulos nativos y proceso de build.
- **Expo Router** convierte archivos dentro de `src/app/` en pantallas.
- **Metro** analiza imports y crea el bundle JavaScript que ejecuta la app.

React Native no renderiza HTML en Android o iOS. Por ejemplo:

```tsx
<View>
  <Text>Hola</Text>
</View>
```

se convierte en vistas y texto nativos. En la versión web, Expo sí proporciona
una traducción equivalente al DOM.

## 2. Estructura del cliente

```text
mobile/
├── app.json                 configuración Expo
├── package.json             dependencias y comandos
├── src/
│   ├── app/                 rutas
│   │   ├── _layout.tsx      providers y navegador raíz
│   │   ├── index.tsx        decide el destino inicial
│   │   ├── (auth)/          rutas públicas
│   │   └── (app)/           rutas autenticadas
│   ├── auth/
│   │   ├── api.ts           traducción HTTP
│   │   ├── AuthProvider.tsx ciclo de vida de la sesión
│   │   ├── tokenStorage.*   almacenamiento por plataforma
│   │   └── types.ts         contratos TypeScript
│   ├── components/          piezas visuales reutilizables
│   └── theme.ts             colores y tipografías
└── assets/                  iconos y splash
```

Los nombres entre paréntesis, como `(auth)`, son grupos de rutas. Organizan el
código sin agregar ese segmento a la URL visible.

## 3. Componentes, JSX y props

Un componente es una función que devuelve JSX:

```tsx
function Greeting({ email }: { email: string }) {
  return <Text>Hola, {email}</Text>;
}
```

`email` es una **prop**: información que el padre entrega al hijo. Las props se
leen, no se modifican. Este proyecto usa componentes como `FormField` y
`PrimaryButton` para evitar repetir estilos y comportamiento.

JSX se parece a HTML, pero es sintaxis de JavaScript. Las llaves introducen una
expresión:

```tsx
<Text>{submitting ? 'Ingresando…' : 'Ingresar'}</Text>
```

## 4. Estado y renderizado

El estado representa información que puede cambiar:

```tsx
const [email, setEmail] = useState('');
```

- `email` contiene el valor actual.
- `setEmail` solicita una actualización.
- React vuelve a ejecutar el componente y dibuja el nuevo resultado.

No se manipula la pantalla de forma imperativa. Se cambia el estado y React
calcula la interfaz correspondiente.

El formulario de login mantiene estado local porque solo esa pantalla necesita
correo, contraseña, error y estado de carga. La sesión es global porque las
rutas, la home y futuras pantallas financieras necesitarán conocer al usuario.

## 5. Context y `AuthProvider`

React Context permite compartir datos sin pasar props por todos los niveles.
`AuthProvider` envuelve el árbol de rutas y publica:

- `session`: usuario y access token actuales.
- `isBootstrapping`: indica si se está restaurando una sesión.
- `signIn` y `signUp`.
- `signOut` y `signOutAll`.
- `refreshProfile`.

Las pantallas lo consumen así:

```tsx
const { session, signIn } = useAuth();
```

No hace falta Redux para este alcance. Una librería de estado se justificaría
cuando aparezcan estados globales independientes y complejos, no antes.

## 6. Navegación por archivos

Expo Router crea una ruta por archivo:

```text
src/app/(auth)/login.tsx    → /login
src/app/(auth)/register.tsx → /register
src/app/(app)/index.tsx     → pantalla autenticada
```

Los `_layout.tsx` definen navegadores y límites. El layout autenticado redirige
al login si no existe sesión. Esto mejora la experiencia, pero no sustituye la
seguridad del backend: un atacante puede modificar su cliente. FastAPI debe
validar el JWT y la propiedad de cada recurso en todas las solicitudes.

## 7. De un botón a un endpoint

El recorrido de login es:

```text
TextInput
  → estado local
  → handleSubmit()
  → AuthProvider.signIn()
  → api.loginUser()
  → fetch(POST /api/v1/auth/login)
  → FastAPI valida el body
  → AuthenticationService verifica Argon2
  → respuesta JSON
  → TypeScript la usa como TokenPair
  → GET /api/v1/auth/me con Bearer token
  → estado de sesión
  → Router muestra la home
```

El cliente HTTP centraliza rutas, headers y JSON. Una pantalla no debería saber
cómo construir `Authorization: Bearer ...`; solo debería pedir `signIn`.

## 8. HTTP, JSON y contratos

Una solicitud tiene método, URL, headers y, a veces, body:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "learner@example.com",
  "password": "synthetic passphrase 2026"
}
```

FastAPI responde con código HTTP y JSON. Los códigos relevantes son:

| Código | Significado en este flujo |
|---|---|
| `200` | Login, refresh o lectura correcta |
| `201` | Usuario creado |
| `204` | Logout correcto, sin body |
| `401` | Credencial o token inválido |
| `409` | El registro no puede completarse |
| `422` | Body inválido según Pydantic |
| `500+` | Error del servidor |

`types.ts` replica el contrato esperado:

```ts
type User = {
  id: string;
  email: string;
  reference_currency: 'ARS' | 'USD';
  created_at: string;
};
```

Esto detecta errores mientras se programa, pero `fetch` puede recibir cualquier
cosa. Pydantic es la validación autoritativa del lado servidor. Si más adelante
se consumen proveedores externos, conviene agregar validación de runtime en el
cliente para sus respuestas no confiables.

## 9. Access token y refresh token

El backend entrega dos credenciales con responsabilidades diferentes.

### Access token

- Es un JWT firmado.
- Dura poco tiempo.
- Se envía como bearer token en endpoints protegidos.
- Permanece solo en memoria dentro de la aplicación.

### Refresh token

- Es opaco: el cliente no interpreta su contenido.
- Dura más tiempo.
- El backend guarda únicamente su hash SHA-256.
- Se almacena en Expo SecureStore en Android/iOS.
- Se reemplaza cada vez que `/refresh` devuelve uno nuevo.

Flujo de renovación:

```text
Solicitud protegida → 401
        ↓
leer refresh token seguro
        ↓
POST /refresh
        ↓
guardar inmediatamente el refresh token nuevo
        ↓
actualizar access token en memoria
        ↓
reintentar una sola vez la solicitud original
```

`AuthProvider` comparte una única promesa de refresh. Si cinco solicitudes
reciben 401 juntas, no deben rotar el mismo token cinco veces; el segundo uso se
interpretaría correctamente como reutilización y revocaría la familia.

## 10. Restauración y logout

Al abrir la app:

1. Se consulta SecureStore.
2. Si no hay refresh token, se muestra login.
3. Si existe, se llama `/refresh`.
4. El token rotado se guarda antes de continuar.
5. `/me` recupera el perfil.
6. Router muestra el grupo autenticado.

Logout del dispositivo revoca su refresh token. Logout global usa el access
token y revoca todas las sesiones del usuario. En ambos casos el secreto local
se elimina incluso si hay un error de red, para que el dispositivo deje de
considerarse autenticado.

El access JWT ya emitido puede seguir siendo válido hasta su vencimiento corto.
Esa limitación está aceptada y documentada en el ADR de autenticación.

## 11. Variables de entorno y conectividad

`EXPO_PUBLIC_API_URL` es configuración pública incluida en el bundle:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.100:8000
```

Nunca debe contener contraseñas, claves JWT ni tokens.

Direcciones habituales:

- Android Emulator: `10.0.2.2` representa la PC anfitriona.
- iOS Simulator: `localhost` suele representar la Mac anfitriona.
- Teléfono físico: necesita la IP LAN de la computadora.
- Producción: URL HTTPS del backend desplegado.

`localhost` en un teléfono físico significa “este teléfono”, no tu PC.

Los navegadores aplican CORS; las aplicaciones nativas no siguen ese mismo
modelo. El MVP móvil no añade una política CORS al backend sin decidir primero
qué orígenes web serán soportados.

## 12. Layout y estilos

React Native usa Flexbox. La dirección predeterminada es vertical, a diferencia
de CSS web. Las unidades son puntos lógicos, no píxeles físicos.

```tsx
const styles = StyleSheet.create({
  row: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
  },
});
```

El proyecto centraliza colores y familias tipográficas en `theme.ts`. Eso no es
solo estética: reduce divergencias y facilita accesibilidad y cambios de marca.

`SafeAreaView` evita cámaras, islas y barras del sistema.
`KeyboardAvoidingView` impide que el teclado tape campos importantes.
`ScrollView` permite completar registro en pantallas pequeñas.

## 13. Async/await y errores

Las llamadas de red son asíncronas. Mientras esperan, la UI sigue respondiendo.

```tsx
try {
  setSubmitting(true);
  await signIn(input);
} catch (error) {
  setMessage(toUserMessage(error));
} finally {
  setSubmitting(false);
}
```

`finally` se ejecuta tanto en éxito como en error. Los botones se deshabilitan
durante la solicitud para impedir envíos duplicados.

No se muestran trazas internas al usuario. `ApiError` traduce fallos de red y
códigos HTTP a mensajes breves sin revelar si un correo específico existe.

## 14. Verificación y depuración

Desde `mobile/`:

```powershell
npm run lint
npm run typecheck
npx expo-doctor
npx expo export --platform android --output-dir dist
npx expo start
```

- **ESLint** busca patrones problemáticos, incluidos hooks mal usados.
- **TypeScript** verifica contratos estáticos.
- **Expo Doctor** compara configuración y dependencias con SDK 57.
- **Expo export** obliga a Metro y Hermes a construir un bundle real.
- **Expo Go** permite probar rápido en un teléfono compatible.

Una prueba completa de autenticación debe cubrir:

1. Registrar un usuario sintético.
2. Entrar y ver `/me`.
3. Cerrar y abrir la app para probar restauración.
4. Esperar o reducir temporalmente la expiración en un entorno de prueba para
   verificar refresh.
5. Cerrar la sesión actual.
6. Abrir dos dispositivos y probar cierre global.
7. Apagar el backend y comprobar el mensaje de red.

## 15. Qué estudiar después

Orden recomendado:

1. Componentes, props y JSX.
2. `useState` y formularios controlados.
3. Renderizado condicional y listas.
4. Promesas, `async`/`await` y `fetch`.
5. Context y separación entre estado local/global.
6. Expo Router y layouts.
7. Pruebas con Jest y React Native Testing Library.
8. Accesibilidad, rendimiento y builds EAS.

Ejercicios sobre este código:

1. Explicar por qué la contraseña es estado local pero la sesión es global.
2. Dibujar el JSON exacto enviado por registro y la respuesta esperada.
3. Identificar qué archivo cambiarías para añadir un endpoint protegido de
   cuentas sin poner lógica HTTP dentro de una pantalla.
4. Explicar por qué ocultar una ruta no protege el backend.
5. Probar qué ocurre cuando `/me` responde 401 y por qué solo se reintenta una
   vez.

## Fuentes oficiales

- [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/)
- [Expo Router](https://docs.expo.dev/router/introduction/)
- [Autenticación en Expo](https://docs.expo.dev/develop/authentication/)
- [Almacenamiento de datos en Expo](https://docs.expo.dev/develop/user-interface/store-data/)
- [Estado en React](https://react.dev/learn/managing-state)
- [Fundamentos de React Native](https://reactnative.dev/docs/getting-started)
