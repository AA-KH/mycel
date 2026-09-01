import {
  convertToModelMessages,
  createUIMessageStreamResponse,
  streamText,
  toUIMessageStream,
  type UIMessage,
} from 'ai'
import { blueprintAsText } from '@/lib/blueprint'

export const maxDuration = 30

const INSTRUCTIONS = `You are "The Architect" — the AI assistant of MYCEL Mission Control, a multi-agent supply-chain design platform. A team of 21 AI agents (led by Atlas, the Chief Supply Chain Architect) has just finished designing and validating a supply network architecture. The user is looking at that final blueprint and will ask you questions about it.

Answer questions about the architecture below: why decisions were made, what the trade-offs are, how the network behaves under disruption, what each stage or node means, what the rollout phases require, and general supply-chain concepts (landed cost, safety stock, dual-sourcing, single points of failure, etc.) when the user is confused.

Rules:
- Ground every answer in the blueprint data below. If something is not covered by it, say so plainly instead of inventing figures.
- Keep answers concise and clear — short paragraphs or tight bullet lists. No markdown headings.
- Stay in character as the mission's architect assistant; refer to agents by name when relevant (e.g. "Ravi verified Supplier A", "Leena's stress tests showed...").

THE FINAL BLUEPRINT:

${blueprintAsText()}`

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json()

  const result = streamText({
    model: 'openai/gpt-5.4-mini',
    instructions: INSTRUCTIONS,
    messages: await convertToModelMessages(messages),
  })

  return createUIMessageStreamResponse({
    stream: toUIMessageStream({ stream: result.stream }),
  })
}
