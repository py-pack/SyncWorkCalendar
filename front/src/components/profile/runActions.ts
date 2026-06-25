// Дескриптори дій «Запустити зараз» на закладці «Синхронізації» (D4/D5).
// Кожен ключ `sync_prefs` → метадані (заголовок/підказка/іконка) + виконавець
// `run(period)`, що кличе НАЯВНІ sync-тригери напряму через `api.*`.
//
// Свідомо БЕЗ стор-дій: run-now із профілю не має перевантажувати таблиці інших
// екранів (D5), тож кличемо клієнт прямо, без побічних `load*`. Мапа в одному
// місці, щоб мінімізувати дрейф із `beat`-диспетчерами (`app/celery_app.py`).
import { api } from '@/api/client'
import type { Period, SyncPrefs, SyncTriggerResult } from '@/api/types'
import type { StringKey } from '@/i18n/strings'

export interface RunAction {
  /** i18n-ключі заголовка й підказки попапа. */
  titleKey: StringKey
  hintKey: StringKey
  /** Іконка кнопки запуску в попапі. */
  icon: string
  /** Дія потребує `worker_key` (бек віддасть `400` без нього, D6). */
  needsWorkerKey: boolean
  /** Виконавець: кличе наявні тригери, повертає фінальний `SyncTriggerResult`.
   *  Для TimeCamp/Jira (D3) — спершу проекти, потім дані за період; дельта
   *  рахується за **другим** (period) викликом. */
  run: (period: Period) => Promise<SyncTriggerResult>
}

export const RUN_ACTIONS: Record<keyof SyncPrefs, RunAction> = {
  // Дзеркалить `beat_pull_timecamp_jira`: проекти TimeCamp → записи за період.
  auto_timecamp_pull: {
    titleKey: 'rsync_tc_title',
    hintKey: 'rsync_tc_hint',
    icon: 'cloudDown',
    needsWorkerKey: false,
    run: async (period) => {
      await api.syncTcProjects() // підготовчий крок; помилка зупиняє дію (D3)
      return api.syncTcEntries(period)
    },
  },
  // Дзеркалить `beat_pull_timecamp_jira`: проекти Jira → задачі за період.
  auto_jira_pull: {
    titleKey: 'rsync_jr_title',
    hintKey: 'rsync_jr_hint',
    icon: 'cloudDown',
    needsWorkerKey: false,
    run: async (period) => {
      await api.syncJrProjects()
      return api.syncJrIssuesAll(period)
    },
  },
  // Дзеркалить `beat_pull_tempo`: worklog-и Tempo за період (потребує worker_key).
  auto_tempo_pull: {
    titleKey: 'rsync_tempo_title',
    hintKey: 'rsync_tempo_hint',
    icon: 'cloudDown',
    needsWorkerKey: true,
    run: (period) => api.syncJrWorklogs(period),
  },
  // Реконсиляція — завжди enqueue (`202 queued`), попап веде в Журнал (D2).
  auto_linking: {
    titleKey: 'rsync_link_title',
    hintKey: 'rsync_link_hint',
    icon: 'link',
    needsWorkerKey: true,
    run: (period) => api.reconcileLinks(period),
  },
  // Пуш у Tempo за період (потребує worker_key).
  auto_push_tempo: {
    titleKey: 'rsync_push_title',
    hintKey: 'rsync_push_hint',
    icon: 'cloudDown',
    needsWorkerKey: true,
    run: (period) => api.syncWstPush(period),
  },
}
