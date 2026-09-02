'use client'

import { useRef, useState } from 'react'
import {
  AgentNote,
  ChipToggle,
  OptionCard,
  RadioRow,
  SectionLabel,
  StepHeading,
  TextAreaField,
  TextField,
  WeightPicker,
} from './fields'
import { PixelButton } from '@/components/pixel/pixel-ui'

export const DEFAULT_PRIORITIES = [
  'Lowest cost',
  'Fastest delivery',
  'Maximum resilience',
  'High product availability',
  'Ability to scale',
  'Sustainability',
  'Domestic sourcing',
  'Consistent quality',
]

export type ConstraintEntry = { category: string; text: string }

export type SetupData = {
  businessType: string
  businessDescription: string
  productName: string
  productDescription: string
  categories: string
  brands: string
  skuRange: string
  customerTypes: string
  supplySource: string
  supplyCountries: string
  operations: string
  operationsDetails: string
  customerScope: string
  customerAreas: string
  volume: string
  demandPattern: string
  peakSurge: string
  timeline: string
  targetDate: string
  deadlineType: string
  budgetTolerance: string
  freightModes: string[]
  priorities: string[]
  constraints: ConstraintEntry[]
  files: string[]
}

export const EMPTY_DATA: SetupData = {
  businessType: '',
  businessDescription: '',
  productName: '',
  productDescription: '',
  categories: '',
  brands: '',
  skuRange: '',
  customerTypes: '',
  supplySource: '',
  supplyCountries: '',
  operations: '',
  operationsDetails: '',
  customerScope: '',
  customerAreas: '',
  volume: '',
  demandPattern: '',
  peakSurge: '',
  timeline: '',
  targetDate: '',
  deadlineType: '',
  budgetTolerance: '',
  freightModes: [],
  priorities: [...DEFAULT_PRIORITIES],
  constraints: [],
  files: [],
}

type StepProps = {
  data: SetupData
  update: (patch: Partial<SetupData>) => void
}

/* ------------------------------------------------ STEP 1 */

const BUSINESS_TYPES = [
  {
    id: 'product',
    title: '01 · Product / Product Line',
    tagline: 'I make or plan to make physical products.',
    description:
      'Design how materials, components, manufacturing, warehousing and distribution should work for one product or a related family.',
  },
  {
    id: 'retail',
    title: '02 · Retail / Ecommerce',
    tagline: 'I buy finished products and sell them to customers.',
    description:
      'You source from brands, manufacturers or wholesalers and sell through one or more stores or online channels.',
  },
  {
    id: 'multi-location',
    title: '03 · Multi-Location Retailer',
    tagline: 'I sell directly through multiple stores or locations.',
    description:
      'Design a network that decides how products are sourced, distributed, stocked and replenished across locations.',
  },
  {
    id: 'wholesaler',
    title: '04 · Wholesaler / Distributor',
    tagline: 'I buy products in bulk and supply other businesses.',
    description:
      'You source from manufacturers and distribute products to retailers, businesses or downstream customers.',
  },
  {
    id: 'multi-category',
    title: '05 · Multi-Product / Multi-Category',
    tagline: 'I handle many products or categories sourced together.',
    description:
      'You need a supply network covering a portfolio of products, categories or brands — not one product or store.',
  },
  {
    id: 'existing',
    title: '06 · Existing Supply Network',
    tagline: 'I already have a supply chain and want to strengthen it.',
    description:
      'You have suppliers, inventory, warehouses or routes and want MYCEL to find weaknesses and design a more resilient network.',
  },
]

export function StepBusinessType({ data, update }: StepProps) {
  const [describing, setDescribing] = useState(data.businessDescription.length > 0)
  return (
    <div>
      <StepHeading kicker="What are you?">What best describes your business?</StepHeading>
      <div className="grid gap-3 sm:grid-cols-2">
        {BUSINESS_TYPES.map((t) => (
          <OptionCard
            key={t.id}
            title={t.title}
            tagline={t.tagline}
            description={t.description}
            selected={data.businessType === t.id}
            onSelect={() => update({ businessType: t.id })}
          />
        ))}
      </div>
      <div className="mt-5 border-t-2 border-dashed border-foreground/30 pt-4">
        {describing ? (
          <TextAreaField
            label="Describe your business"
            value={data.businessDescription}
            onChange={(v) => update({ businessDescription: v })}
            placeholder="e.g. I run a bathroom fittings business. We buy from manufacturers in Gujarat and distribute to hardware shops across Punjab."
          />
        ) : (
          <button
            type="button"
            onClick={() => setDescribing(true)}
            className="font-mono text-[10px] uppercase tracking-widest text-accent underline underline-offset-4 hover:text-foreground"
          >
            {'Not sure which one fits? Describe your business instead ->'}
          </button>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 2 */

export function StepSupplying({ data, update }: StepProps) {
  const t = data.businessType
  const isMaker = t === 'product'
  const isExisting = t === 'existing'
  const isWholesaler = t === 'wholesaler'
  const isRetailer = !isMaker && !isExisting && !isWholesaler

  return (
    <div>
      <StepHeading kicker="What are you supplying?">
        {isMaker
          ? 'What are you producing?'
          : isWholesaler
            ? 'What products will you distribute?'
            : isExisting
              ? 'What does your current network handle?'
              : 'What will you sell?'}
      </StepHeading>
      <div className="flex flex-col gap-4">
        {isMaker ? (
          <>
            <TextField
              label="Product name"
              value={data.productName}
              onChange={(v) => update({ productName: v })}
              placeholder="e.g. Graphite pencils"
            />
            <TextAreaField
              label="Product description"
              value={data.productDescription}
              onChange={(v) => update({ productDescription: v })}
              placeholder="What is it, what is it made of, who is it for?"
              rows={3}
            />
            <TextField
              label="Product categories / product lines"
              value={data.categories}
              onChange={(v) => update({ categories: v })}
              placeholder="e.g. Stationery, art supplies"
            />
            <div className="mt-2 rounded-sm border-2 border-dashed border-foreground/30 bg-muted/30 p-4">
              <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Optional — Upload at the last step:
              </p>
              <ul className="list-inside list-disc text-sm text-muted-foreground marker:text-accent">
                <li>BOM / product specifications</li>
              </ul>
            </div>
          </>
        ) : isExisting ? (
          <div>
            <TextAreaField
              label="What does your current network handle?"
              value={data.productDescription}
              onChange={(v) => update({ productDescription: v })}
              placeholder="Products handled, suppliers, warehouses, routes..."
              rows={4}
            />
            <div className="mt-4 rounded-sm border-2 border-dashed border-foreground/30 bg-muted/30 p-4">
              <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Optional — Upload at the last step:
              </p>
              <ul className="list-inside list-disc text-sm text-muted-foreground marker:text-accent">
                <li>SKU list</li>
                <li>Supplier list</li>
                <li>Inventory data</li>
                <li>Sales history</li>
                <li>Warehouse information</li>
              </ul>
              <p className="mt-2 text-sm text-muted-foreground">if available.</p>
            </div>
          </div>
        ) : (
          <>
            <TextField
              label={isWholesaler ? 'Categories' : 'Product categories'}
              value={data.categories}
              onChange={(v) => update({ categories: v })}
              placeholder="e.g. Bathroom fittings, sanitaryware"
            />
            <TextField
              label={isWholesaler ? 'Brands' : 'Known brands / products'}
              value={data.brands}
              onChange={(v) => update({ brands: v })}
              placeholder="e.g. Jaquar, Hindware"
              optional
            />
            <div>
              <SectionLabel>Approximate number of SKUs</SectionLabel>
              <div className="flex flex-wrap gap-2">
                {['< 50', '50 – 500', '500 – 5,000', '5,000+', 'Not sure'].map((r) => (
                  <ChipToggle
                    key={r}
                    label={r}
                    selected={data.skuRange === r}
                    onToggle={() => update({ skuRange: r })}
                  />
                ))}
              </div>
            </div>
            {isWholesaler ? (
              <TextField
                label="Typical customer types"
                value={data.customerTypes}
                onChange={(v) => update({ customerTypes: v })}
                placeholder="e.g. Hardware shops, contractors, institutions"
              />
            ) : null}
          </>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 3 */

export function StepWhere({ data, update }: StepProps) {
  return (
    <div>
      <StepHeading kicker="Where?">Where does the network operate?</StepHeading>
      <div className="flex flex-col gap-6">
        <div>
          <SectionLabel>Supply — where can you source from?</SectionLabel>
          <div className="flex flex-col gap-2">
            {['India only', 'India + international', 'Specific countries', 'No preference'].map(
              (o) => (
                <RadioRow
                  key={o}
                  label={o}
                  selected={data.supplySource === o}
                  onSelect={() => update({ supplySource: o })}
                />
              ),
            )}
          </div>
          {data.supplySource === 'Specific countries' ? (
            <div className="mt-3">
              <TextField
                label="Which countries?"
                value={data.supplyCountries}
                onChange={(v) => update({ supplyCountries: v })}
                placeholder="e.g. India, Vietnam, Germany"
              />
            </div>
          ) : null}
        </div>

        <div>
          <SectionLabel>Operations — manufacturing / warehouse locations</SectionLabel>
          <div className="flex flex-col gap-2">
            {['Existing locations', 'Planned locations', 'None yet'].map((o) => (
              <RadioRow
                key={o}
                label={o}
                selected={data.operations === o}
                onSelect={() => update({ operations: o })}
              />
            ))}
          </div>
          {data.operations && data.operations !== 'None yet' ? (
            <div className="mt-3">
              <TextField
                label="Where?"
                value={data.operationsDetails}
                onChange={(v) => update({ operationsDetails: v })}
                placeholder="e.g. Factory in Baddi, warehouse in Delhi"
              />
            </div>
          ) : null}
        </div>

        <div>
          <SectionLabel>Customers — where do you sell / distribute?</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {['City', 'State', 'Region', 'Country', 'Multiple countries'].map((o) => (
              <ChipToggle
                key={o}
                label={o}
                selected={data.customerScope === o}
                onToggle={() => update({ customerScope: o })}
              />
            ))}
          </div>
          <div className="mt-3">
            <TextField
              label="Name the areas"
              value={data.customerAreas}
              onChange={(v) => update({ customerAreas: v })}
              placeholder="e.g. Punjab, Haryana, Delhi NCR"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 4 */

const VOLUME_OPTIONS: Record<string, string[]> = {
  product: ['< 1,000 units/month', '1,000 – 10,000', '10,000 – 100,000', '100,000+', 'Not sure'],
  wholesaler: ['Small', 'Medium', 'Large', 'Enterprise', 'Not sure'],
  default: ['< ₹1L / month', '₹1 – 10L', '₹10 – 50L', '₹50L+', 'Not sure'],
}

export function StepScale({ data, update }: StepProps) {
  const options =
    VOLUME_OPTIONS[data.businessType === 'product' ? 'product' : data.businessType === 'wholesaler' ? 'wholesaler' : 'default']
  const label =
    data.businessType === 'product'
      ? 'Expected production'
      : data.businessType === 'wholesaler'
        ? 'Expected distribution volume'
        : 'Expected sales'
  return (
    <div>
      <StepHeading kicker="How much?">How much does your network need to support?</StepHeading>
      <p className="mb-5 text-sm leading-relaxed text-muted-foreground">
        {"Don't force exact numbers — ranges are enough."}
      </p>
      <div className="flex flex-col gap-6">
        <div>
          <SectionLabel>{label}</SectionLabel>
          <div className="flex flex-col gap-2">
            {options.map((o) => (
              <RadioRow
                key={o}
                label={o}
                selected={data.volume === o}
                onSelect={() => update({ volume: o })}
              />
            ))}
          </div>
        </div>
        <div>
          <SectionLabel>Demand pattern — is demand:</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {['Stable', 'Seasonal', 'Highly variable', 'Growing rapidly', 'Unknown'].map((o) => (
              <ChipToggle
                key={o}
                label={o}
                selected={data.demandPattern === o}
                onToggle={() => update({ demandPattern: o })}
              />
            ))}
          </div>
        </div>
        <div>
          <SectionLabel>Peak surge — at your busiest, volume can spike to:</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {['~ Same as usual', '2x normal', '5x normal', '10x or more', 'Not sure'].map((o) => (
              <ChipToggle
                key={o}
                label={o}
                selected={data.peakSurge === o}
                onToggle={() => update({ peakSurge: o })}
              />
            ))}
          </div>
        </div>
        <AgentNote agent="Ethan" role="Independent validator">
          Ethan stress-tests your network at these volumes. The gap between normal and peak decides
          how much slack capacity the blueprint must survive.
        </AgentNote>
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 5 — TIMELINE */

const TIMELINE_OPTIONS = [
  {
    label: 'As soon as possible',
    sublabel: 'Network should be operational within weeks.',
  },
  {
    label: 'Fixed launch date',
    sublabel: 'A specific event or date — e.g. Black Friday, Diwali, a product launch.',
  },
  {
    label: 'This quarter',
    sublabel: 'Within the next ~3 months.',
  },
  {
    label: '6 – 12 months',
    sublabel: 'A longer runway — we can phase the rollout.',
  },
  {
    label: 'Flexible',
    sublabel: 'No hard target — optimize for the best network, not the calendar.',
  },
]

export function StepTimeline({ data, update }: StepProps) {
  return (
    <div>
      <StepHeading kicker="By when?">When does this network need to be live?</StepHeading>
      <p className="mb-5 text-sm leading-relaxed text-muted-foreground">
        A hard date changes everything — supplier onboarding, freight choices and rollout phases
        all get sequenced backwards from it.
      </p>
      <div className="flex flex-col gap-6">
        <div>
          <SectionLabel>Launch target</SectionLabel>
          <div className="flex flex-col gap-2">
            {TIMELINE_OPTIONS.map((o) => (
              <RadioRow
                key={o.label}
                label={o.label}
                sublabel={o.sublabel}
                selected={data.timeline === o.label}
                onSelect={() => update({ timeline: o.label })}
              />
            ))}
          </div>
          {data.timeline === 'Fixed launch date' ? (
            <div className="mt-3">
              <TextField
                label="Which date or event?"
                value={data.targetDate}
                onChange={(v) => update({ targetDate: v })}
                placeholder="e.g. Black Friday 2026 / 15 March 2027"
              />
            </div>
          ) : null}
        </div>
        <div>
          <SectionLabel>How hard is this deadline?</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {['Immovable — we miss it, we lose', 'Strong preference', 'Soft target'].map((o) => (
              <ChipToggle
                key={o}
                label={o}
                selected={data.deadlineType === o}
                onToggle={() => update({ deadlineType: o })}
              />
            ))}
          </div>
        </div>
        <AgentNote agent="Priya" role="Implementation planner">
          Priya builds your rollout plan backwards from this date. An immovable deadline compresses
          her phases and rules out slow options before Rohan even prices them.
        </AgentNote>
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 6 — BUDGET TOLERANCE */

const BUDGET_OPTIONS = [
  {
    label: 'Strictly lowest cost',
    sublabel: 'Every rupee counts. Slow-but-cheap routes win — think sea freight, consolidated loads.',
    badge: 'Cost first',
  },
  {
    label: 'Balanced',
    sublabel: 'Prefer cheap, but pay a premium where it clearly protects speed or resilience.',
    badge: 'Default',
  },
  {
    label: 'Speed over cost',
    sublabel: 'Premium options like air freight are on the table when they hit the deadline.',
    badge: 'Speed first',
  },
  {
    label: 'Cost is secondary',
    sublabel: 'Reliability and availability matter far more than the freight bill.',
    badge: 'Resilience',
  },
]

export function StepBudget({ data, update }: StepProps) {
  const toggleMode = (m: string) =>
    update({
      freightModes: data.freightModes.includes(m)
        ? data.freightModes.filter((x) => x !== m)
        : [...data.freightModes, m],
    })

  return (
    <div>
      <StepHeading kicker="At what cost?">How much cost pressure can the network take?</StepHeading>
      <p className="mb-5 text-sm leading-relaxed text-muted-foreground">
        This sets the trade-off rules — whether we route your goods on a 30-day sea lane or a
        3-day air corridor.
      </p>
      <div className="flex flex-col gap-6">
        <div>
          <SectionLabel>Budget tolerance</SectionLabel>
          <div className="flex flex-col gap-2">
            {BUDGET_OPTIONS.map((o) => (
              <RadioRow
                key={o.label}
                label={o.label}
                sublabel={o.sublabel}
                badge={o.badge}
                selected={data.budgetTolerance === o.label}
                onSelect={() => update({ budgetTolerance: o.label })}
              />
            ))}
          </div>
        </div>
        <div>
          <SectionLabel>Freight modes you are open to (pick any)</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {['Sea', 'Rail', 'Road', 'Air', 'No preference'].map((m) => (
              <ChipToggle
                key={m}
                label={m}
                selected={data.freightModes.includes(m)}
                onToggle={() => toggleMode(m)}
              />
            ))}
          </div>
        </div>
        <AgentNote agent="Rohan" role="Master supply-chain architect">
          Rohan uses this to choose between routes. {'"Strictly lowest cost"'} locks him to sea and
          road; {'"speed over cost"'} unlocks premium air corridors when your deadline demands it.
        </AgentNote>
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 7 — PRIORITIES */

export function StepPriorities({ data, update }: StepProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    // Required for Firefox to allow drag
    e.dataTransfer.setData('text/plain', index.toString())
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    setDragOverIndex(index)
  }

  const handleDrop = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === targetIndex) {
      setDraggedIndex(null)
      setDragOverIndex(null)
      return
    }

    const newPriorities = [...data.priorities]
    const [draggedItem] = newPriorities.splice(draggedIndex, 1)
    newPriorities.splice(targetIndex, 0, draggedItem)

    update({ priorities: newPriorities })
    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  const move = (index: number, direction: -1 | 1) => {
    const newPriorities = [...data.priorities]
    const targetIndex = index + direction
    if (targetIndex < 0 || targetIndex >= newPriorities.length) return
    
    const temp = newPriorities[index]
    newPriorities[index] = newPriorities[targetIndex]
    newPriorities[targetIndex] = temp
    
    update({ priorities: newPriorities })
  }

  return (
    <div>
      <StepHeading kicker="What matters?">
        What should your supply network optimize for?
      </StepHeading>
      <p className="mb-5 text-sm leading-relaxed text-muted-foreground">
        Arrange in order of priority. Top items matter the most. Drag and drop to reorder.
      </p>
      <div className="flex flex-col gap-2">
        {data.priorities.map((p, index) => {
          const isDragging = draggedIndex === index
          const isOver = dragOverIndex === index && draggedIndex !== null && draggedIndex !== index
          
          return (
            <div 
              key={p} 
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
              className={`flex items-center justify-between border-2 px-4 py-2 cursor-grab active:cursor-grabbing transition-colors ${
                isDragging ? 'opacity-40 border-dashed border-foreground/50 bg-background' 
                : isOver ? 'border-accent bg-accent/10 border-dashed'
                : 'border-foreground bg-card'
              }`}
            >
              <span className="text-sm font-medium flex items-center">
                <span className="font-mono text-[10px] text-muted-foreground mr-3 cursor-grab flex items-center gap-2">
                  <span className="flex flex-col gap-0.5 opacity-50">
                    <span className="w-1 h-1 bg-current rounded-full" />
                    <span className="w-1 h-1 bg-current rounded-full" />
                    <span className="w-1 h-1 bg-current rounded-full" />
                  </span>
                  {index + 1}.
                </span>
                {p}
              </span>
              <div className="flex gap-1">
                <button
                  type="button"
                  disabled={index === 0}
                  onClick={() => move(index, -1)}
                  className="flex h-7 w-7 items-center justify-center border-2 border-transparent bg-muted text-foreground transition-colors hover:border-foreground disabled:opacity-30 disabled:hover:border-transparent"
                  aria-label={`Move ${p} up`}
                >
                  ▲
                </button>
                <button
                  type="button"
                  disabled={index === data.priorities.length - 1}
                  onClick={() => move(index, 1)}
                  className="flex h-7 w-7 items-center justify-center border-2 border-transparent bg-muted text-foreground transition-colors hover:border-foreground disabled:opacity-30 disabled:hover:border-transparent"
                  aria-label={`Move ${p} down`}
                >
                  ▼
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ------------------------------------------------ STEP 8 — CONSTRAINTS */

const CONSTRAINT_CATEGORIES = [
  'Existing suppliers',
  'Existing contracts',
  'Discounts',
  'Existing warehouses',
  'Existing manufacturing',
  'Logistics agreements',
  'Supplier preferences',
  'Hard constraints',
]

export function StepConstraints({ data, update }: StepProps) {
  const [category, setCategory] = useState(CONSTRAINT_CATEGORIES[0])
  const [text, setText] = useState('')

  const add = () => {
    if (!text.trim()) return
    update({ constraints: [...data.constraints, { category, text: text.trim() }] })
    setText('')
  }

  return (
    <div>
      <StepHeading kicker="What do we already know?">
        {"What should we know that the internet can't tell us?"}
      </StepHeading>
      <p className="mb-5 text-sm leading-relaxed text-muted-foreground">
        {'Existing relationships, contracts, discounts, facilities and hard limits — e.g. "We have a 2-year contract with Supplier Y" or "Maximum acceptable lead time is 20 days."'}
      </p>
      <SectionLabel>Pick a category</SectionLabel>
      <div className="mb-4 flex flex-wrap gap-2">
        {CONSTRAINT_CATEGORIES.map((c) => (
          <ChipToggle key={c} label={c} selected={category === c} onToggle={() => setCategory(c)} />
        ))}
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <TextField
            label={category}
            value={text}
            onChange={setText}
            placeholder='e.g. "We already buy graphite from X" / "Products must be FSC certified"'
          />
        </div>
        <PixelButton type="button" variant="orange" onClick={add} className="shrink-0">
          + Add
        </PixelButton>
      </div>
      {data.constraints.length > 0 ? (
        <ul className="mt-5 flex flex-col gap-2">
          {data.constraints.map((c, i) => (
            <li
              key={i}
              className="flex items-start justify-between gap-3 border-2 border-foreground bg-card px-3 py-2.5"
            >
              <div>
                <span className="block font-mono text-[8px] uppercase tracking-widest text-accent">
                  {c.category}
                </span>
                <span className="text-sm">{c.text}</span>
              </div>
              <button
                type="button"
                aria-label={`Remove constraint: ${c.text}`}
                onClick={() =>
                  update({ constraints: data.constraints.filter((_, j) => j !== i) })
                }
                className="border-2 border-foreground bg-background px-2 py-0.5 font-mono text-[10px] hover:bg-destructive hover:text-accent-foreground"
              >
                x
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------ STEP 9 — UPLOAD */

const FILE_TYPES = [
  'Supplier list',
  'Inventory report',
  'Sales history',
  'Product catalogue',
  'BOM',
  'Contracts',
  'Network diagram',
]

export function StepUpload({ data, update }: StepProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setUploading(true)
    setError(null)
    
    try {
      const { getToken, uploadDocument } = await import('@/lib/auth')
      const token = getToken()
      if (!token) throw new Error("No session found")
      
      const newUrls: string[] = []
      for (const file of Array.from(files)) {
        const result = await uploadDocument(token, file)
        newUrls.push(result.cloudinary_url)
      }
      
      update({ files: [...data.files, ...newUrls] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <StepHeading kicker="Upload your data">
        Add anything you already have — we will read it.
      </StepHeading>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          onFiles(e.dataTransfer.files)
        }}
        className="flex w-full flex-col items-center gap-3 border-4 border-dashed border-foreground/50 bg-card px-6 py-12 transition-colors hover:border-accent hover:bg-muted"
      >
        <span className="border-2 border-foreground bg-secondary px-4 py-2 font-mono text-[10px] uppercase tracking-widest pixel-shadow-sm">
          {uploading ? 'Uploading...' : '+ Add files'}
        </span>
        <span className="text-sm text-muted-foreground">
          Drag &amp; drop or click — CSV, Excel, PDF
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".csv,.xlsx,.xls,.pdf"
        className="sr-only"
        onChange={(e) => onFiles(e.target.files)}
        aria-label="Upload data files"
      />
      <div className="mt-5">
        <SectionLabel>Useful documents</SectionLabel>
        <div className="flex flex-wrap gap-2">
          {FILE_TYPES.map((f) => (
            <span
              key={f}
              className="border-2 border-foreground/40 bg-background px-3 py-1.5 font-mono text-[8px] uppercase tracking-widest text-muted-foreground"
            >
              {f}
            </span>
          ))}
        </div>
      </div>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      {data.files.length > 0 ? (
        <ul className="mt-5 flex flex-col gap-2">
          {data.files.map((f, i) => (
            <li
              key={`${f}-${i}`}
              className="flex items-center justify-between gap-3 border-2 border-foreground bg-card px-3 py-2.5"
            >
              <span className="flex items-center gap-2 text-sm">
                <span className="h-2.5 w-2.5 bg-secondary" aria-hidden="true" />
                {f}
              </span>
              <button
                type="button"
                aria-label={`Remove file ${f}`}
                onClick={() => update({ files: data.files.filter((_, j) => j !== i) })}
                className="border-2 border-foreground bg-background px-2 py-0.5 font-mono text-[10px] hover:bg-destructive hover:text-accent-foreground"
              >
                x
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
