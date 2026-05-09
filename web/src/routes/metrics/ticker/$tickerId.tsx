import {
  Anchor,
  Badge,
  Box,
  Breadcrumbs,
  Group,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { createFileRoute, Link, notFound } from '@tanstack/react-router'
import { IconTrendingDown, IconTrendingUp } from '@tabler/icons-react'

import { getTicker } from '../../../data/tickers'

export const Route = createFileRoute('/metrics/ticker/$tickerId')({
  loader: ({ params }) => {
    const ticker = getTicker(params.tickerId)
    if (!ticker) throw notFound()
    return ticker
  },
  component: TickerDetail,
  notFoundComponent: () => (
    <Stack py="md" gap="md">
      <Title order={2}>Ticker not found</Title>
      <Anchor component={Link} to="/metrics">
        Back to metrics
      </Anchor>
    </Stack>
  ),
})

function TickerDetail() {
  const ticker = Route.useLoaderData()
  const up = ticker.change >= 0
  const Icon = up ? IconTrendingUp : IconTrendingDown
  const color = up ? 'gain' : 'brand'

  return (
    <Stack gap="lg" py="md">
      <Breadcrumbs>
        <Anchor component={Link} to="/metrics" c="dimmed">
          Metrics
        </Anchor>
        <Text c="dimmed">{ticker.id}</Text>
      </Breadcrumbs>

      <Group justify="space-between" align="flex-start">
        <Stack gap={4}>
          <Text
            fw={900}
            fz={64}
            lh={1}
            ff='"Fraunces", serif'
            style={{ letterSpacing: '-0.03em' }}
          >
            {ticker.id}
          </Text>
          <Text size="md" c="dimmed" fw={500}>
            {ticker.name}
          </Text>
        </Stack>
        <Badge size="lg" color={color} variant="light" radius="sm" leftSection={<Icon size={16} />}>
          {up ? '+' : ''}
          {ticker.changePercent.toFixed(2)}%
        </Badge>
      </Group>

      <Group gap="xl">
        <Stack gap={2}>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600} style={{ letterSpacing: '0.08em' }}>
            Current
          </Text>
          <Text fw={700} fz={28} ff="monospace" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {ticker.value.toLocaleString()}
          </Text>
        </Stack>
        <Stack gap={2}>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600} style={{ letterSpacing: '0.08em' }}>
            Change
          </Text>
          <Text fw={700} fz={28} ff="monospace" c={color} style={{ fontVariantNumeric: 'tabular-nums' }}>
            {up ? '+' : ''}
            {ticker.change.toLocaleString()}
          </Text>
        </Stack>
      </Group>

      <Paper withBorder p="xl" radius="lg">
        <Box h={400} style={{ display: 'grid', placeItems: 'center' }}>
          <Stack align="center" gap="xs">
            <Text c="dimmed">Chart coming soon</Text>
            <Text size="xs" c="dimmed">
              Lightweight Charts will render {ticker.id} history here.
            </Text>
          </Stack>
        </Box>
      </Paper>

      <Text c="dimmed">{ticker.description}</Text>
    </Stack>
  )
}
