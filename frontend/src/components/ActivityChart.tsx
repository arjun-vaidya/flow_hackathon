import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Opportunity } from '../data/opportunities'

export default function ActivityChart({
  activity,
}: {
  activity: Opportunity['activity']
}) {
  return (
    <div
      className="chart"
      role="img"
      aria-label={`Synthetic monthly contributions: ${activity.map((point) => `${point.month} ${point.contributions}`).join(', ')}`}
    >
      <ResponsiveContainer width="100%" height={190}>
        <BarChart
          data={activity}
          margin={{ top: 20, right: 10, left: -25, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 5"
            vertical={false}
            stroke="#e8ebe6"
          />
          <XAxis
            dataKey="month"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: '#7b817a' }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: '#7b817a' }}
          />
          <Tooltip cursor={{ fill: '#eff3ed' }} />
          <Bar
            name="Demo contributions"
            dataKey="contributions"
            fill="#476e56"
            radius={[4, 4, 0, 0]}
            maxBarSize={42}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
