/* =========================================================================
   Sync Work — i18n composable поверх ui.lang (stores/ui)
   Використання: const { t, lang, setLang } = useI18n();  {{ t.auth_signin }}
   (`t` — computed; у шаблоні Vue авто-розгортає ref, тож t.key працює).
   ========================================================================= */
import { computed, type ComputedRef } from 'vue'

import { useUiStore } from '@/stores/ui'

import { STRINGS, type Lang, type Strings } from './strings'

export { STRINGS }
export type { Lang, Strings }

export function useI18n(): {
  t: ComputedRef<Strings>
  lang: ComputedRef<Lang>
  setLang: (lang: Lang) => void
} {
  const ui = useUiStore()
  return {
    t: computed(() => STRINGS[ui.lang]),
    lang: computed(() => ui.lang),
    setLang: (lang: Lang) => ui.setLang(lang),
  }
}
