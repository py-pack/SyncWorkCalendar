/* =========================================================================
   Sync Work — UI-store (тема, мова, акцент, щільність, календарні твіки,
   згорнутість навігації, поточний маршрут). Персист — через storage-обгортку
   (dot-path ui.*); застосування data-theme і токенів акценту до <html>.
   ========================================================================= */
import { defineStore } from 'pinia'
import { watch } from 'vue'

import type { Lang } from '@/i18n/strings'
import { applyAccent, DEFAULT_ACCENT, type Theme } from '@/styles/palette'
import { useStored } from '@/lib/storage'

export type Density = 'compact' | 'regular'

export const useUiStore = defineStore('ui', () => {
  const theme = useStored<Theme>('ui.theme', 'light')
  const lang = useStored<Lang>('ui.lang', 'uk')
  const accent = useStored<string>('ui.accent', DEFAULT_ACCENT)
  const density = useStored<Density>('ui.density', 'regular')
  const workBand = useStored<boolean>('ui.workBand', true)
  const weekends = useStored<boolean>('ui.weekends', true)
  const navCollapsed = useStored<boolean>('ui.navCollapsed', false)
  const route = useStored<string>('ui.route', 'calendar')

  // застосувати тему + акцент до <html> (одразу і на кожну зміну)
  watch(
    theme,
    (v) => document.documentElement.setAttribute('data-theme', v),
    { immediate: true },
  )
  watch(
    [accent, theme],
    () => applyAccent(accent.value, theme.value),
    { immediate: true },
  )

  function toggleTheme(): void {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  function setLang(value: Lang): void {
    lang.value = value
  }
  function setAccent(value: string): void {
    accent.value = value
  }
  function setDensity(value: Density): void {
    density.value = value
  }
  function toggleNav(): void {
    navCollapsed.value = !navCollapsed.value
  }
  function setRoute(value: string): void {
    route.value = value
  }

  return {
    theme, lang, accent, density, workBand, weekends, navCollapsed, route,
    toggleTheme, setLang, setAccent, setDensity, toggleNav, setRoute,
  }
})
