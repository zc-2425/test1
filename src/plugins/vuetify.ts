import 'vuetify/styles'
import { createVuetify, type ThemeDefinition } from 'vuetify'
import { zhHans } from 'vuetify/locale'

/**
 * 主题令牌直接对齐 docs/04-设计令牌.md。
 * 说明：设计稿是「M3 风格但不纯 M3」——保留 M3 的色板/圆角/outlined 表单，
 * 但 hover 是橙色、侧栏激活是整行直角（后两项在组件里手写覆盖，不走主题）。
 */
const aiLight: ThemeDefinition = {
  dark: false,
  colors: {
    background: '#FFFBFF',
    surface: '#FFFBFF',
    'surface-bright': '#FFFBFF',
    'surface-light': '#F7F2FA',
    'surface-variant': '#F3EDF7',
    'on-surface': '#322F32',
    'on-surface-variant': '#5D5A5D',
    'surface-tint': '#6750A4',

    primary: '#6750A4',
    'primary-darken-1': '#57428E',
    'primary-lighten-1': '#8571BF',
    'on-primary': '#FFFFFF',
    'primary-container': '#EADDFF',

    secondary: '#625B71',
    'on-secondary': '#FFFFFF',
    tertiary: '#7D5260',
    'on-tertiary': '#FFFFFF',

    error: '#BA1A1A',
    'on-error': '#FFFFFF',
    'error-container': '#FFDAD6',
    info: '#1976D2',
    'on-info': '#FFFFFF',
    success: '#2E7D32',
    'on-success': '#FFFFFF',
    warning: '#F57C00',
    'on-warning': '#FFFFFF',

    // 设计稿自有扩展色：用 $vuetify.theme.current.colors['row-hover'] 访问
    outline: '#CAC4D0',
    'outline-variant': '#E8E3E7',
    divider: '#E8E3E7',
    'table-header': '#FAFAFA',
    'row-hover': '#FFF4E5',
    'accent-hover': '#F57C00',
    'sidebar-bg': '#FEF7FF',
    'sidebar-divider': '#DBD8DC',
    'sidebar-text': '#43525A',
    'status-running': '#1B88CA',
    'status-neutral': '#969598',
    'auth-start': '#6878E2',
    'auth-end': '#7551AA'
  },
  variables: {
    'border-color': '#CAC4D0',
    'border-opacity': 1,
    'border-radius-root': '12px',
    'rounded-0': '0px',
    'rounded-sm': '8px',
    rounded: '12px',
    'rounded-lg': '16px',
    'rounded-xl': '24px',
    'high-emphasis-opacity': 0.92,
    'medium-emphasis-opacity': 0.68,
    'disabled-opacity': 0.38,
    'hover-opacity': 0.08,
    'focus-opacity': 0.12,
    'pressed-opacity': 0.12
  }
}

export default createVuetify({
  locale: {
    locale: 'zhHans',
    fallback: 'en',
    messages: { zhHans }
  },
  theme: {
    defaultTheme: 'aiLight',
    themes: { aiLight }
  },
  defaults: {
    VBtn: { rounded: 'lg', elevation: 0, variant: 'flat' },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      hideDetails: 'auto',
      color: 'primary'
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
      hideDetails: 'auto',
      color: 'primary'
    },
    VSelect: { variant: 'outlined', density: 'comfortable', hideDetails: 'auto', color: 'primary' },
    VAutocomplete: {
      variant: 'outlined',
      density: 'comfortable',
      hideDetails: 'auto',
      color: 'primary'
    },
    VSwitch: { inset: true, color: 'primary', hideDetails: true },
    VCard: { elevation: 0, rounded: 'lg', border: true },
    VChip: { rounded: 'pill', variant: 'outlined' },
    VDialog: { scrim: 'rgba(0,0,0,0.4)', maxWidth: 560 },
    VMenu: { offset: [0, 4] }
  }
})
