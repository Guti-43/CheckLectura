from __future__ import annotations

from fastapi import Request

TRANSLATIONS = {
    'it': {
        'Ese nombre no nos suena. Prueba otra vez.': 'Questo nome non ci risulta. Riprova.',
        'Contraseña incorrecta.': 'Password non corretta.',
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
