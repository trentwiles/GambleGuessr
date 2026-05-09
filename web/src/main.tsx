import '@mantine/core/styles.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import {
  MantineProvider,
  createTheme,
  localStorageColorSchemeManager,
  type MantineColorsTuple,
} from '@mantine/core'
import { RouterProvider, createRouter } from '@tanstack/react-router'

import { routeTree } from './routeTree.gen'

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const SANS = '"DM Sans", ui-sans-serif, system-ui, -apple-system, sans-serif'
const SERIF =
  '"Fraunces", ui-serif, Georgia, "Times New Roman", serif'
const MONO =
  '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace'

const brand: MantineColorsTuple = [
  '#ffe9eb',
  '#ffc7cb',
  '#ff9ba2',
  '#ff6e78',
  '#f54c57',
  '#ee3f4a',
  '#d12c37',
  '#ad202b',
  '#7a131b',
  '#4d0a10',
]

const gain: MantineColorsTuple = [
  '#e6f7fa',
  '#c0eaf0',
  '#92dde6',
  '#62cfdb',
  '#34c4d2',
  '#00b9cc',
  '#00859b',
  '#006478',
  '#004555',
  '#002934',
]

const dark: MantineColorsTuple = [
  '#E1E1E1',
  '#A6A7AB',
  '#909296',
  '#5C5F66',
  '#2A2A2A',
  '#161616',
  '#0A0A0A',
  '#000000',
  '#000000',
  '#000000',
]

const theme = createTheme({
  primaryColor: 'brand',
  primaryShade: { light: 5, dark: 5 },
  fontFamily: SANS,
  fontFamilyMonospace: MONO,
  headings: {
    fontFamily: SERIF,
    fontWeight: '800',
  },
  defaultRadius: 'md',
  colors: { brand, gain, dark },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider
      theme={theme}
      defaultColorScheme="dark"
      colorSchemeManager={localStorageColorSchemeManager({
        key: 'gambleguessr-color-scheme',
      })}
    >
      <RouterProvider router={router} />
    </MantineProvider>
  </StrictMode>,
)
