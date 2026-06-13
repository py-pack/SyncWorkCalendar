/* =========================================================================
   Sync Work — палітри кольорів (перенесено з прототипу data.jsx / app.jsx)
   - projectColors(hue): oklch-набір на один проект (фіксовані L/C, змінний H);
   - ACCENTS: 5 акцентів × (light/dark) для рантайм-перепису --accent* змінних.
   ========================================================================= */

export type Theme = 'light' | 'dark'

/** Один відтінок (hue) на проект — гармонійний oklch-набір. */
export function projColor(hue: number, l: number, c: number): string {
  return `oklch(${l} ${c} ${hue})`
}

export interface ProjectColors {
  base: string
  strong: string
  soft: string
  softDark: string
  ink: string
  inkLight: string
}

export function projectColors(hue: number): ProjectColors {
  return {
    base: projColor(hue, 0.62, 0.13),
    strong: projColor(hue, 0.55, 0.15),
    soft: projColor(hue, 0.95, 0.035),
    softDark: projColor(hue, 0.28, 0.05),
    ink: projColor(hue, 0.42, 0.13),
    inkLight: projColor(hue, 0.8, 0.11),
  }
}

/** Палітра акценту: a=accent, p=press, s=soft, i=ink. */
export interface AccentSet {
  a: string
  p: string
  s: string
  i: string
}

/** Доступні акценти (ключ = базовий колір з палітри Tweaks). */
export const ACCENTS: Record<string, { l: AccentSet; d: AccentSet }> = {
  '#2a6fdb': { l: { a: '#2a6fdb', p: '#245fbd', s: '#e9f0fc', i: '#1b4fa0' }, d: { a: '#5a92e8', p: '#6c9eed', s: '#1a2740', i: '#aecbf6' } },
  '#1f8a5b': { l: { a: '#1f8a5b', p: '#1a7a50', s: '#e4f4ec', i: '#13633f' }, d: { a: '#46c485', p: '#5bd095', s: '#13291f', i: '#9fe6c2' } },
  '#6b53d6': { l: { a: '#6b53d6', p: '#5d46c0', s: '#ece9fb', i: '#4a37a0' }, d: { a: '#9c8cf0', p: '#a89af3', s: '#211b3a', i: '#cfc6f8' } },
  '#475569': { l: { a: '#475569', p: '#3b4757', s: '#eef1f5', i: '#2f3b4d' }, d: { a: '#8fa0b8', p: '#9fb0c6', s: '#1c2330', i: '#c4cfde' } },
  '#c2700a': { l: { a: '#c2700a', p: '#a85f08', s: '#fbefdc', i: '#8a4f07' }, d: { a: '#e0a04e', p: '#e8ad60', s: '#2e2414', i: '#f0cd95' } },
}

/** Порядок акцентів для палітри Tweaks. */
export const ACCENT_OPTIONS = Object.keys(ACCENTS)
export const DEFAULT_ACCENT = '#2a6fdb'

/** Застосувати палітру акценту до CSS-змінних на <html>. */
export function applyAccent(accent: string, theme: Theme): void {
  const set = (ACCENTS[accent] ?? ACCENTS[DEFAULT_ACCENT])[theme === 'dark' ? 'd' : 'l']
  const r = document.documentElement.style
  r.setProperty('--accent', set.a)
  r.setProperty('--accent-press', set.p)
  r.setProperty('--accent-soft', set.s)
  r.setProperty('--accent-ink', set.i)
}
