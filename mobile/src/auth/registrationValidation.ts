export type RegistrationErrors = {
  email?: string;
  password?: string;
  confirmation?: string;
};

export function validateRegistration(
  email: string,
  password: string,
  confirmation: string,
): RegistrationErrors {
  const errors: RegistrationErrors = {};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
    errors.email = 'Ingresá un correo válido, por ejemplo nombre@correo.com.';
  }

  const passwordLength = Array.from(password).length;
  if (passwordLength < 8) {
    errors.password = 'La contraseña debe tener al menos 8 caracteres.';
  } else if (passwordLength > 128) {
    errors.password = 'La contraseña no puede superar los 128 caracteres.';
  }

  if (!confirmation) {
    errors.confirmation = 'Repetí la contraseña para confirmarla.';
  } else if (password !== confirmation) {
    errors.confirmation = 'Las contraseñas no coinciden.';
  }
  return errors;
}
