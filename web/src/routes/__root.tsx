import {
  ActionIcon,
  Anchor,
  AppShell,
  Button,
  Container,
  Group,
  Text,
  useMantineColorScheme,
} from '@mantine/core'
import { IconMoon, IconSun, IconUserCircle } from '@tabler/icons-react'
import { createRootRoute, Link, Outlet } from '@tanstack/react-router'

type NavItem =
  | { label: string; to: '/metrics'; active: true }
  | { label: string; active: false }

const NAV: NavItem[] = [
  { label: 'Metrics', to: '/metrics', active: true },
  { label: 'Markets', active: false },
  { label: 'Watchlist', active: false },
  { label: 'History', active: false },
  { label: 'Research', active: false },
]

function ColorSchemeToggle() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme()
  const dark = colorScheme === 'dark'
  return (
    <ActionIcon
      onClick={toggleColorScheme}
      variant="subtle"
      size="lg"
      color="gray"
      aria-label="Toggle color scheme"
    >
      {dark ? <IconSun size={18} /> : <IconMoon size={18} />}
    </ActionIcon>
  )
}

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header
        withBorder
        style={{ backdropFilter: 'saturate(180%) blur(4px)' }}
      >
        <Group h="100%" px="lg" justify="space-between" wrap="nowrap">
          <Group gap="xl" wrap="nowrap">
            <Text
              fw={900}
              fz={24}
              ff='"Fraunces", serif'
              style={{ letterSpacing: '-0.03em' }}
            >
              GambleGuessr
            </Text>
            <Group gap="lg" wrap="nowrap" visibleFrom="sm">
              {NAV.map((item) =>
                item.active ? (
                  <Anchor
                    key={item.label}
                    component={Link}
                    to={item.to}
                    size="sm"
                    fw={500}
                    underline="never"
                    activeProps={{
                      style: { color: 'var(--mantine-color-brand-5)' },
                    }}
                  >
                    {item.label}
                  </Anchor>
                ) : (
                  <Text
                    key={item.label}
                    component="span"
                    size="sm"
                    fw={500}
                    c="dimmed"
                    style={{ cursor: 'not-allowed' }}
                    title="Coming soon"
                  >
                    {item.label}
                  </Text>
                ),
              )}
            </Group>
          </Group>
          <Group gap="sm" wrap="nowrap">
            <ColorSchemeToggle />
            <Button
              size="sm"
              variant="filled"
              radius="xl"
              fw={600}
              leftSection={<IconUserCircle size={16} />}
            >
              Login
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Container size="xl">
          <Outlet />
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}
