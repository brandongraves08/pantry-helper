import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Package } from 'lucide-react'
import DashboardStat from '../components/DashboardStat'

describe('DashboardStat', () => {
  it('renders title and value', () => {
    render(
      <DashboardStat
        icon={Package}
        title="Total Items"
        value={42}
        subtitle="+12% from last week"
      />
    )
    expect(screen.getByText('Total Items')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('+12% from last week')).toBeInTheDocument()
  })

  it('renders value zero', () => {
    render(
      <DashboardStat
        icon={Package}
        title="Empty"
        value={0}
      />
    )
    expect(screen.getByText('Empty')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders loading skeleton when loading', () => {
    const { container } = render(
      <DashboardStat
        icon={Package}
        title="Loading"
        value={42}
        loading={true}
      />
    )
    expect(screen.getByText('Loading')).toBeInTheDocument()
    expect(container.querySelector('.skeleton')).toBeInTheDocument()
  })

  it('renders icon with correct color', () => {
    const { container } = render(
      <DashboardStat
        icon={Package}
        title="Stock"
        value={5}
        iconColor="text-green-600"
      />
    )
    const iconWrap = container.querySelector('.text-green-600')
    expect(iconWrap).toBeInTheDocument()
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})
