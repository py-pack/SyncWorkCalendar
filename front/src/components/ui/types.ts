// Спільні типи UI-примітивів (виносимо з SFC, бо <script setup> не дозволяє
// export-декларацій).

export interface MenuItem {
  label?: string
  icon?: string
  hint?: string
  onClick?: () => void
  disabled?: boolean
  danger?: boolean
  divider?: boolean
}

export interface SegmentedOption<V extends string = string> {
  value: V
  label?: string
  icon?: string
  title?: string
}
