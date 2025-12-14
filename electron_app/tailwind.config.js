/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 马卡龙可爱配色
        primary: '#FF6B8B', // 蜜桃粉（主色）
        secondary: '#82C3EC', // 天空蓝（辅助色）
        accent: '#FFD166', // 奶油黄（强调色）
        mint: '#93E9BE', // 薄荷绿（点缀色）
        dark: '#F9F7F7', // 浅灰白（深色模式底）
        darker: '#FFFFFF', // 纯白（深色模式分层）
        neutral: '#F0EEF8', // 淡紫灰（组件背景）
        'neutral-light': '#E8E5F8', // 浅紫灰（hover状态）
        'text-primary': '#4A4A68', // 深紫灰（主文本）
        'text-secondary': '#9492A6', // 浅紫灰（次文本）
        // Dark 模式（柔和暗色调）
        'dark-bg': '#2D2B40',
        'dark-neutral': '#3D3B56',
        'dark-text-primary': '#F9F7F7',
        'dark-text-secondary': '#C0BED9',
      },
      fontFamily: {
        sans: ['Comic Neue', 'system-ui', 'sans-serif'], // 卡通字体
      },
      boxShadow: {
        'cute': '0 4px 12px rgba(255, 107, 139, 0.15)',
        'cute-hover': '0 6px 18px rgba(255, 107, 139, 0.25)',
        'float': '0 8px 20px rgba(130, 195, 236, 0.2)',
      },
      animation: {
        'bounce-slow': 'bounce 3s infinite',
        'wiggle': 'wiggle 1s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-2deg)' },
          '50%': { transform: 'rotate(2deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        }
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
        'pill': '9999px',
      }
    },
  },
  plugins: [],
}