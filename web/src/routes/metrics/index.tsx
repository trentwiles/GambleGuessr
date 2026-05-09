import { createFileRoute } from '@tanstack/react-router'
import { SimpleGrid, Stack, Text, Title } from '@mantine/core'

import { TICKERS } from '../../data/tickers'
import { TickerCard } from '../../components/TickerCard'

export const Route = createFileRoute('/metrics/')({
  component: MetricsPage,
})

function MetricsPage() {
  return (
    <Stack gap="xl" py="md">
      <Stack gap={4}>
        <Title order={1}>Metrics</Title>
        <Text c="dimmed">
          Skill ratings, averages, and rolling stats — quoted as live tickers.
        </Text>
      </Stack>
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
        {TICKERS.map((t) => (
          <TickerCard key={t.id} ticker={t} />
        ))}
      </SimpleGrid>
    </Stack>
  )
}
