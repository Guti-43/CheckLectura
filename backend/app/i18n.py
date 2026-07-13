from __future__ import annotations

from fastapi import Request

TRANSLATIONS = {
    'it': {
        'Ese nombre no nos suena. Prueba otra vez.': 'Questo nome non ci risulta. Riprova.',
        'Contraseña incorrecta.': 'Password non corretta.',
        'Nombre o contraseña incorrectos.': 'Nome o password non corretti.',
        '¿Aún no tienes cuenta?': 'Non hai ancora un account?', 'Crear cuenta': 'Crea account',
        'Cuenta nueva': 'Nuovo account', 'Únete a CheckLectura': 'Unisciti a CheckLectura',
        'Elige tu nombre y contraseña para empezar.': 'Scegli nome e password per iniziare.',
        'Ese nombre ya está pillado.': 'Questo nome è già in uso.',
        'Escribe un nombre y una contraseña válidos.': 'Inserisci un nome e una password validi.',
        '¿Ya tienes cuenta?': 'Hai già un account?', 'Entrar': 'Entra',
        'plan': 'piano', 'planes': 'piani', 'usuario': 'utente', 'usuarios': 'utenti',
        'caps/dia': 'cap./giorno', 'dias completados': 'giorni completati',
        'dias leidos': 'giorni letti', 'dias': 'giorni', 'Mejor racha:': 'Migliore serie:',
        'Semana': 'Settimana',
        'Tu nota': 'La tua nota', 'Escribe aquí lo que te hayas quedado pensando...': 'Scrivi qui ciò che ti è rimasto in mente...',
        'Guardar nota': 'Salva nota', 'Elige un día': 'Scegli un giorno', 'Te quedan': 'Ti restano', 'día': 'giorno', 'días': 'giorni', 'Al día ✨': 'In pari ✨',
    },
    'en': {
        'Ese nombre no nos suena. Prueba otra vez.': 'We do not recognize that name. Try again.',
        'Contraseña incorrecta.': 'Incorrect password.',
        'Nombre o contraseña incorrectos.': 'Incorrect name or password.',
        '¿Aún no tienes cuenta?': 'Do not have an account yet?', 'Crear cuenta': 'Create account',
        'Cuenta nueva': 'New account', 'Únete a CheckLectura': 'Join CheckLectura',
        'Elige tu nombre y contraseña para empezar.': 'Choose your name and password to get started.',
        'Ese nombre ya está pillado.': 'That name is already taken.',
        'Escribe un nombre y una contraseña válidos.': 'Enter a valid name and password.',
        '¿Ya tienes cuenta?': 'Already have an account?', 'Entrar': 'Log in',
        'plan': 'plan', 'planes': 'plans', 'usuario': 'user', 'usuarios': 'users',
        'caps/dia': 'chapters/day', 'dias completados': 'days completed',
        'dias leidos': 'days read', 'dias': 'days', 'Mejor racha:': 'Best streak:',
        'Semana': 'Week',
        'Tu nota': 'Your note', 'Escribe aquí lo que te hayas quedado pensando...': 'Write down what stayed with you...',
        'Guardar nota': 'Save note', 'Elige un día': 'Choose a day', 'Te quedan': 'You have', 'día': 'day', 'días': 'days', 'Al día ✨': 'All caught up ✨',
    },
}


def translate(value: str, request: Request) -> str:
    language = request.cookies.get('checklectura-language', 'es')
    return TRANSLATIONS.get(language, {}).get(value, value)
