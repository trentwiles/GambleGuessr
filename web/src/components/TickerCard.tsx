import { Card, Group, Text, Badge, Stack } from '@mantine/core'
import { Link } from '@tanstack/react-router'
import { IconTrendingDown, IconTrendingUp } from '@tabler/icons-react'

import type { Ticker } from '../data/tickers'

function formatValue(n: number): string {
  if (Math.abs(n) < 10) return n.toFixed(3)
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

export function TickerCard({ ticker }: { ticker: Ticker }) {
  const up = ticker.change >= 0
  const Icon = up ? IconTrendingUp : IconTrendingDown
  const color = up ? 'gain' : 'brand'

  return (
    <Link
      to="/metrics/ticker/$tickerId"
      params={{ tickerId: ticker.id }}
      style={{ textDecoration: 'none', color: 'inherit' }}
    >
      <Card withBorder padding="lg" radius="lg" shadow="sm">
        <Stack gap="sm">
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <Stack gap={2}>
              <Text
                fw={800}
                fz={32}
                lh={1}
                ff='"Fraunces", serif'
                style={{ letterSpacing: '-0.02em' }}
              >
                {ticker.id}
              </Text>
              <Text size="sm" c="dimmed" fw={500}>
                {ticker.name}
              </Text>
            </Stack>
            <Badge
              color={color}
              variant="light"
              radius="sm"
              leftSection={<Icon size={14} />}
            >
              {up ? '+' : ''}
              {ticker.changePercent.toFixed(2)}%
            </Badge>
          </Group>

          <Group justify="space-between" align="baseline">
            <Text fw={700} fz={26} ff="monospace" style={{ fontVariantNumeric: 'tabular-nums' }}>
              {formatValue(ticker.value)}
            </Text>
            <Text size="sm" c={color} ff="monospace" fw={600}>
              {up ? '+' : ''}
              {formatValue(ticker.change)}
            </Text>
          </Group>

          <Text size="xs" c="dimmed" lineClamp={2}>
            {ticker.description}
          </Text>
        </Stack>
      </Card>
    </Link>
  )
}
