import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import prettier from 'eslint-config-prettier'

export default tseslint.config(
  {
    ignores: ['dist/**', 'node_modules/**', '_ref/**', 'docs/**', 'coverage/**', '*.min.js']
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser
      }
    }
  },
  {
    // TS 本身就会查未定义标识符（window / Event / HTMLSelectElement 由 DOM lib 提供），
    // 在 TS 项目里再开 no-undef 只会制造噪音 —— 这也是 typescript-eslint 的官方建议
    files: ['**/*.{ts,vue}'],
    rules: {
      'no-undef': 'off'
    }
  },
  {
    rules: {
      // 页面级组件用单名（LoginView / AppShell）不符合多词规则，关掉
      'vue/multi-word-component-names': 'off',
      // 可选 prop 用 `?` 标注即可，不必再写默认值（TS 类型已表达清楚）
      'vue/require-default-prop': 'off',
      // 属性顺序交给 prettier 与人工判断
      'vue/attributes-order': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-self-closing': [
        'error',
        {
          html: { void: 'always', normal: 'always', component: 'always' },
          svg: 'always',
          math: 'always'
        }
      ],
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
      'no-debugger': 'error'
    }
  },
  {
    // Node 脚本（开发工具）：flat config 不像 eslintrc 那样自带 env，
    // 这里显式声明用到的 Node 全局，避免为了几个 global 再装一个 globals 包
    files: ['scripts/**/*.{js,mjs}', '*.config.js'],
    languageOptions: {
      globals: {
        process: 'readonly',
        console: 'readonly',
        Buffer: 'readonly',
        URL: 'readonly',
        WebSocket: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        __dirname: 'readonly'
      }
    },
    rules: {
      'no-console': 'off'
    }
  },
  {
    files: ['**/*.d.ts'],
    rules: {
      '@typescript-eslint/no-empty-object-type': 'off'
    }
  },
  prettier
)
