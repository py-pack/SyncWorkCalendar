// Спільні типи табличного каркасу (винесено з SFC — `<script setup>` не
// дозволяє export-декларацій).

export interface Column {
  key: string
  label: string
  /** число → px; рядок → as-is (напр. '20%'). */
  width?: number | string
  align?: 'left' | 'right'
  mono?: boolean
}

export interface TabItem {
  id: string
  label: string
  icon?: string
  count?: number
}
